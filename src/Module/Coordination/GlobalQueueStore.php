<?php
declare(strict_types=1);

namespace Ezs\Web\Module\Coordination;

use PDO;

/**
 * Single application-agnostic durable queue kernel.
 * No live worker, HTTP endpoint or automatic expired-lease reclamation.
 */
final class GlobalQueueStore
{
    private PDO $db;

    public function __construct(string $path)
    {
        if (!extension_loaded('pdo_sqlite')) {
            throw new \RuntimeException('pdo_sqlite_required');
        }
        $dir = dirname($path);
        if (!is_dir($dir) && !mkdir($dir, 0700, true) && !is_dir($dir)) {
            throw new \RuntimeException('queue_directory_unavailable');
        }
        $this->db = new PDO('sqlite:'.$path, null, null, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_TIMEOUT => 5,
        ]);
        $this->db->exec('PRAGMA busy_timeout=5000');
        $this->db->exec('PRAGMA journal_mode=WAL');
        $this->db->exec('PRAGMA foreign_keys=ON');
        $this->db->exec("CREATE TABLE IF NOT EXISTS global_queue_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producer TEXT NOT NULL,
            external_id TEXT NOT NULL,
            idempotency_key TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL,
            resource_class TEXT NOT NULL CHECK(resource_class IN ('cpu','gpu')),
            priority INTEGER NOT NULL CHECK(priority BETWEEN 0 AND 100),
            state TEXT NOT NULL CHECK(state IN ('queued','running','completed','failed')),
            lease_token TEXT,
            lease_until INTEGER,
            claim_generation INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            UNIQUE(producer,external_id)
        )");
        $this->db->exec('CREATE INDEX IF NOT EXISTS global_queue_pick ON global_queue_jobs(state,resource_class,priority DESC,created_at,id)');
        $this->db->exec("CREATE TABLE IF NOT EXISTS global_queue_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            producer TEXT NOT NULL,
            event_type TEXT NOT NULL CHECK(event_type IN ('progress','heartbeat','warning','error')),
            progress_percent INTEGER CHECK(progress_percent IS NULL OR progress_percent BETWEEN 0 AND 99),
            phase TEXT,
            message TEXT,
            created_at INTEGER NOT NULL,
            FOREIGN KEY(job_id) REFERENCES global_queue_jobs(id)
        )");
        $this->db->exec('CREATE INDEX IF NOT EXISTS global_queue_event_by_producer ON global_queue_events(producer,event_id)');
    }

    /** Enqueue is idempotent for identical immutable technical envelopes. */
    public function enqueue(string $producer, string $externalId, string $key, string $kind, string $resourceClass, int $priority = 50): array
    {
        foreach ([$producer,$externalId,$key,$kind] as $value) {
            if ($value === '' || strlen($value) > 128 || preg_match('/[\x00-\x1f\x7f]/', $value)) {
                throw new \InvalidArgumentException('invalid_queue_identity');
            }
        }
        if (!in_array($resourceClass, ['cpu','gpu'], true) || $priority < 0 || $priority > 100) {
            throw new \InvalidArgumentException('invalid_queue_capability');
        }
        return $this->transaction(function () use ($producer,$externalId,$key,$kind,$resourceClass,$priority): array {
            $now = time();
            $stmt = $this->db->prepare("INSERT OR IGNORE INTO global_queue_jobs (producer,external_id,idempotency_key,kind,resource_class,priority,state,created_at,updated_at) VALUES (?,?,?,?,?,?,'queued',?,?)");
            $stmt->execute([$producer,$externalId,$key,$kind,$resourceClass,$priority,$now,$now]);
            $row=$this->byKey($key);
            if ($row===null || $row['producer']!==$producer || $row['external_id']!==$externalId || $row['kind']!==$kind || $row['resource_class']!==$resourceClass || (int)$row['priority']!==$priority) {
                throw new \DomainException('queue_identity_collision');
            }
            return $row;
        });
    }

    /** Atomic claim for a compatible worker; never steals a running lease. */
    public function claim(string $resourceClass, int $leaseSeconds = 120): ?array
    {
        if (!in_array($resourceClass, ['cpu','gpu'],true) || $leaseSeconds < 5 || $leaseSeconds > 3600) {
            throw new \InvalidArgumentException('invalid_claim');
        }
        return $this->transaction(function () use ($resourceClass,$leaseSeconds): ?array {
            $q=$this->db->prepare("SELECT id FROM global_queue_jobs WHERE state='queued' AND resource_class=? ORDER BY priority DESC,created_at ASC,id ASC LIMIT 1");
            $q->execute([$resourceClass]);$id=$q->fetchColumn();
            if ($id===false) return null;
            $token=bin2hex(random_bytes(32));
            $now=time();
            $u=$this->db->prepare("UPDATE global_queue_jobs SET state='running',lease_token=?,lease_until=?,claim_generation=claim_generation+1,updated_at=? WHERE id=? AND state='queued'");
            $u->execute([$token,$now+$leaseSeconds,$now,(int)$id]);
            if ($u->rowCount()!==1) throw new \RuntimeException('claim_conflict');
            return $this->byId((int)$id);
        });
    }

    /** A live lease holder alone may finalize. Result payload remains owned by producer. */
    public function finish(int $id,string $token,bool $success): array
    {
        if ($id<=0 || !preg_match('/^[a-f0-9]{64}$/D',$token)) throw new \InvalidArgumentException('invalid_completion');
        return $this->transaction(function () use ($id,$token,$success): array {
            $row=$this->byId($id);
            if ($row===null || $row['state']!=='running' || !hash_equals((string)$row['lease_token'],$token) || (int)$row['lease_until'] < time()) {
                throw new \DomainException('lease_not_current');
            }
            $state=$success?'completed':'failed';
            $stmt=$this->db->prepare("UPDATE global_queue_jobs SET state=?,lease_token=NULL,lease_until=NULL,updated_at=? WHERE id=? AND lease_token=? AND state='running'");
            $stmt->execute([$state,time(),$id,$token]);
            if ($stmt->rowCount()!==1) throw new \RuntimeException('completion_conflict');
            return $this->byId($id);
        });
    }


    /**
     * Worker-owned progress or heartbeat. No fabricated percentage or business interpretation.
     * Heartbeats extend leases; progress remains monotonic (when supplied).
     */
    public function heartbeat(int $id, string $token, int $leaseSeconds = 120, ?int $percent = null, ?string $phase = null, ?string $message = null): array
    {
        if ($id <= 0 || !preg_match('/^[a-f0-9]{64}$/D', $token) || $leaseSeconds < 5 || $leaseSeconds > 3600) {
            throw new \InvalidArgumentException('invalid_heartbeat');
        }
        if ($percent !== null && ($percent < 0 || $percent > 99)) throw new \InvalidArgumentException('invalid_progress');
        if (($phase !== null && (strlen($phase) > 96 || preg_match('/[\x00-\x1f\x7f]/', $phase)))
            || ($message !== null && (strlen($message) > 240 || preg_match('/[\x00-\x1f\x7f]/', $message)))) {
            throw new \InvalidArgumentException('invalid_progress_text');
        }
        return $this->transaction(function () use ($id,$token,$leaseSeconds,$percent,$phase,$message): array {
            $row=$this->byId($id);
            $now=time();
            if ($row===null || $row['state']!=='running' || !hash_equals((string)$row['lease_token'],$token)
                || (int)$row['lease_until'] < $now) throw new \DomainException('lease_not_current');
            if ($percent!==null) {
                $query=$this->db->prepare("SELECT MAX(progress_percent) FROM global_queue_events WHERE job_id=? AND progress_percent IS NOT NULL");
                $query->execute([$id]);
                $previous=$query->fetchColumn();
                if ($previous!==null && $previous!==false && $percent < (int)$previous) throw new \DomainException('progress_regression');
            }
            $up=$this->db->prepare("UPDATE global_queue_jobs SET lease_until=?,updated_at=? WHERE id=? AND lease_token=? AND state='running'");
            $up->execute([$now+$leaseSeconds,$now,$id,$token]);
            if ($up->rowCount()!==1) throw new \RuntimeException('heartbeat_conflict');
            $event=$this->db->prepare('INSERT INTO global_queue_events(job_id,producer,event_type,progress_percent,phase,message,created_at) VALUES (?,?,?,?,?,?,?)');
            $event->execute([$id,$row['producer'],$percent===null?'heartbeat':'progress',$percent,$phase,$message,$now]);
            return ['job_id'=>$id,'lease_until'=>$now+$leaseSeconds,'event_id'=>(int)$this->db->lastInsertId(),'progress_percent'=>$percent];
        });
    }

    /** Cursor-based immutable event read, scoped by producer. Never expose lease secrets. */
    public function events(string $producer, int $after = 0, int $limit = 100): array
    {
        if ($producer==='' || strlen($producer)>128 || $after<0 || $limit<1 || $limit>100) {
            throw new \InvalidArgumentException('invalid_event_query');
        }
        $q=$this->db->prepare('SELECT event_id,job_id,event_type,progress_percent,phase,message,created_at FROM global_queue_events WHERE producer=? AND event_id>? ORDER BY event_id ASC LIMIT ?');
        $q->bindValue(1,$producer,PDO::PARAM_STR);
        $q->bindValue(2,$after,PDO::PARAM_INT);
        $q->bindValue(3,$limit,PDO::PARAM_INT);
        $q->execute();
        return $q->fetchAll(PDO::FETCH_ASSOC);
    }

    public function byId(int $id): ?array
    {
        $s=$this->db->prepare('SELECT * FROM global_queue_jobs WHERE id=?');$s->execute([$id]);
        return $s->fetch(PDO::FETCH_ASSOC)?:null;
    }

    private function byKey(string $key): ?array
    {
        $s=$this->db->prepare('SELECT * FROM global_queue_jobs WHERE idempotency_key=?');$s->execute([$key]);
        return $s->fetch(PDO::FETCH_ASSOC)?:null;
    }

    private function transaction(\Closure $callback): mixed
    {
        $this->db->exec('BEGIN IMMEDIATE');
        try {
            $value=$callback();$this->db->commit();return $value;
        } catch (\Throwable $e) {
            if ($this->db->inTransaction()) $this->db->rollBack();
            throw $e;
        }
    }
}
