<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Infrastructure;

/** Gestion Windows native et conservative, sans shell ni PowerShell. */
final class NativeWindowsLifecycle
{
    private const ROOT = 'H:/EZS_orchestrator';
    private const PHP_CGI = 'H:/PHP/php-8.5-x64/php-cgi.exe';
    private const CADDY = 'H:/Caddy/caddy.exe';
    private const DEV = [
        'root_php' => ['port'=>8791,'exe'=>self::PHP_CGI,'cwd'=>self::ROOT,'args'=>'-b 127.0.0.1:8791'],
        'root_caddy' => ['port'=>8790,'exe'=>self::CADDY,'cwd'=>self::ROOT,'args'=>'run --config "H:/EZS_orchestrator/config/caddy/Caddyfile.dev-lab-assistant-candidate" --adapter caddyfile'],
        'ezscore_dev' => ['port'=>8602,'exe'=>self::PHP_CGI,'cwd'=>'H:/EZScore_dev','args'=>'-b 127.0.0.1:8602'],
        'ezscore_preview' => ['port'=>8862,'exe'=>self::PHP_CGI,'cwd'=>'H:/EZScore_dev','args'=>'-b 127.0.0.1:8862'],
        'lab' => ['port'=>8701,'exe'=>self::PHP_CGI,'cwd'=>'H:/EZStudio_lab','args'=>'-b 127.0.0.1:8701'],
        'assistant' => ['port'=>8713,'exe'=>self::PHP_CGI,'cwd'=>'H:/EZStudioLab_assistant','args'=>'-b 127.0.0.1:8713'],
    ];
    /** PROD : un seul Caddy expose les trois facades, deux FastCGI distincts.
     * Le backend Symfony conserve APP_ENV=prod / APP_DEBUG=0 et son SSO. */
    private const PROD = [
        'prod_backend' => ['port'=>8512,'exe'=>self::PHP_CGI,'cwd'=>'H:/EZScore','args'=>'-b 127.0.0.1:8512'],
        'prod_gateway' => ['port'=>18515,'exe'=>self::PHP_CGI,'cwd'=>self::ROOT.'/runtime_components/prod_gateway_php','args'=>'-b 127.0.0.1:18515'],
        'prod_caddy' => ['port'=>8501,'additional_ports'=>[8510,8511], 'exe'=>self::CADDY,'cwd'=>self::ROOT,
            'args'=>'run --config "H:/EZS_orchestrator/config/caddy/Caddyfile.prod" --adapter caddyfile'],
    ];
    /** @var list<resource> Process handles held until the CLI exits. */
    private static array $spawnHandles = [];
    private readonly \Closure $inventory;
    private readonly \Closure $listeners;
    private readonly \Closure $spawn;
    private readonly \Closure $terminate;
    private readonly \Closure $dependencyAvailable;
    private readonly \Closure $activeOwner;
    private readonly string $runtime;
    private readonly string $profile;
    private readonly array $managedSpecs;

    /** Callbacks de test uniquement ; toutes opérations réelles utilisent les API Windows. */
    public function __construct(?callable $inventory=null, ?callable $listeners=null, ?callable $spawn=null, ?callable $terminate=null, ?string $runtime=null, ?callable $dependencyAvailable=null, ?callable $activeOwner=null, string $profile='dev')
    {
        $this->inventory=$inventory ? \Closure::fromCallable($inventory) : static fn():array=>(new WindowsProcessInventory())->collect();
        $this->listeners=$listeners ? \Closure::fromCallable($listeners) : self::nativeListeners(...);
        $this->spawn=$spawn ? \Closure::fromCallable($spawn) : self::nativeSpawn(...);
        $this->terminate=$terminate ? \Closure::fromCallable($terminate) : self::nativeTerminate(...);
        if(!in_array($profile,['dev','prod'],true))throw new \InvalidArgumentException('EZS_NATIVE_PROFILE_REFUSED');
        $this->profile=$profile;
        $this->managedSpecs=$profile==='prod' ? self::PROD : self::DEV;
        $this->runtime=$runtime ?? self::ROOT.'/runtime/v2-'.$profile;
        $this->dependencyAvailable=$dependencyAvailable ? \Closure::fromCallable($dependencyAvailable) : static fn(string $exe,string $cwd):bool=>is_file($exe) && is_dir($cwd);
        $this->activeOwner=$activeOwner ? \Closure::fromCallable($activeOwner) : WindowsActiveTcpProof::owner(...);
    }
    public static function specs():array { return self::DEV; }
    public static function prodSpecs():array { return self::PROD; }
    private function schema():string { return 'ezs.native.'.$this->profile.'.v1'; }
    private static function portsOf(array $spec):array
    { return [$spec['port'],...($spec['additional_ports']??[])]; }
    /** Un journal d'intention non résolu bloque toute nouvelle mutation. */
    private function assertNoPending():void
    {
        if (is_file($this->runtime.'/native-spawn-pending.json'))
            throw new \RuntimeException('EZS_NATIVE_PENDING_REQUIRES_MANUAL_ATTESTATION');
    }
    /** Après une interruption, ne lever un pending que si aucun processus candidat ne subsiste. */
    private function reconcilePending():void
    {
        $path=$this->runtime.'/native-spawn-pending.json';
        if(!is_file($path))return;
        $raw=file_get_contents($path);
        $data=is_string($raw)?json_decode($raw,true):null;
        $name=is_array($data)?($data['name']??null):null;
        if(($data['schema']??null)!=='ezs.native.pending.v1' || !is_string($name) || !isset($this->managedSpecs[$name]))
            throw new \RuntimeException('EZS_NATIVE_PENDING_INVALID');
        $spec=$this->managedSpecs[$name];
        for($i=0;$i<2;$i++){
            [$processes,$ports]=$this->observations();
            if(self::occupied($spec,$ports))throw new \RuntimeException('EZS_NATIVE_PENDING_PORT_ACTIVE_'.$name);
            foreach($processes as $pid=>$observed){
                $record=['pid'=>$pid,'created'=>(string)($observed['created']??'')];
                $candidatePorts=$ports;
                foreach(self::portsOf($spec) as $port)$candidatePorts[$port]=[$pid];
                if(self::attest($record,$spec,$observed,$candidatePorts))
                    throw new \RuntimeException('EZS_NATIVE_PENDING_PROCESS_ACTIVE_'.$name);
            }
            if($i===0)usleep(200000);
        }
        $line=gmdate('c').' ABANDONED_PENDING '.$name."\n";
        if(file_put_contents($this->runtime.'/native-reconciled.log',$line,FILE_APPEND|LOCK_EX)===false)
            throw new \RuntimeException('EZS_NATIVE_RECONCILIATION_LOG_FAILED');
        if(!unlink($path))throw new \RuntimeException('EZS_NATIVE_PENDING_CLEAR_FAILED');
    }

    /** Maintenance explicite des états orphelins, sous verrou exclusif. */
    public function reconcile():void
    {
        $this->withLock(function():void {
            $this->reconcilePending();
            $this->reconcileLegacy();
            $stored=$this->records();
            [$processes,$ports]=$this->observations();
            $this->reconcileDeadRecords($stored,$processes,$ports);
        });
    }
    private function pending(string $name):void
    {
        $path=$this->runtime.'/native-spawn-pending.json';
        $bytes=json_encode(['schema'=>'ezs.native.pending.v1','name'=>$name,'time'=>gmdate('c')],JSON_THROW_ON_ERROR);
        if(file_put_contents($path,$bytes,LOCK_EX)===false)
            throw new \RuntimeException('EZS_NATIVE_PENDING_WRITE_FAILED');
    }
    private function clearPending():void
    {
        $path=$this->runtime.'/native-spawn-pending.json';
        if(!is_file($path) || !unlink($path))
            throw new \RuntimeException('EZS_NATIVE_PENDING_CLEAR_FAILED');
    }
    private function records():array
    {
        $file=$this->runtime.'/native-processes.json';
        if(!is_file($file)) return [];
        $data=json_decode((string)file_get_contents($file),true,512,JSON_THROW_ON_ERROR);
        if(!is_array($data) || ($data['schema']??'')!==$this->schema() || !is_array($data['records']??null))
            throw new \RuntimeException('EZS_NATIVE_STATE_INVALID');
        return $data['records'];
    }
    private function persist(array $records):void
    {
        if(!is_dir($this->runtime)) throw new \RuntimeException('EZS_NATIVE_RUNTIME_MISSING');
        $temp=$this->runtime.'/native-processes.json.'.bin2hex(random_bytes(8)).'.tmp';
        $bytes=json_encode(['schema'=>$this->schema(),'records'=>$records],JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR);
        if(file_put_contents($temp,$bytes,LOCK_EX)===false || !rename($temp,$this->runtime.'/native-processes.json'))
            throw new \RuntimeException('EZS_NATIVE_STATE_SAVE_FAILED');
    }
    private function withLock(callable $task):mixed
    {
        if(!is_dir($this->runtime)) throw new \RuntimeException('EZS_NATIVE_RUNTIME_MISSING');
        $h=fopen($this->runtime.'/native-lifecycle.lock','c+');
        if(!$h || !flock($h,LOCK_EX|LOCK_NB)) throw new \RuntimeException('EZS_NATIVE_BUSY');
        try{return $task();}finally{flock($h,LOCK_UN);fclose($h);}
    }
    private static function index(array $rows):array
    {
        $out=[];
        foreach($rows as $p){$pid=(int)($p['pid']??0);if($pid>0)$out[$pid]=$p;}
        return $out;
    }
    public static function attest(array $record,array $spec,array $observed,array $ports):bool
    {
        $pid=(int)($record['pid']??0);
        if($pid<1 || $pid!==(int)($observed['pid']??0))return false;
        $created=(string)($record['created']??'');
        if($created==='' || $created!==(string)($observed['created']??''))return false;
        $norm=static fn(string $s):string=>strtolower(str_replace('/','\\',$s));
        if($norm((string)($observed['executable']??''))!==$norm($spec['exe']))return false;
        // Windows may quote each proc_open(array) argument independently in WMI.
        // Compare the COMPLETE command, not a substring; extra arguments are refused.
        $tokenPattern=static function(string $token) use ($norm):string {
            $quoted=preg_quote($norm($token),'~');
            return '(?:"'.$quoted.'"|'.$quoted.')';
        };
        try {$tokens=self::spawnArguments($spec['args']);}
        catch (\InvalidArgumentException) {return false;}
        $pieces=[$tokenPattern($spec['exe'])];
        foreach($tokens as $token)$pieces[]=$tokenPattern($token);
        $pattern='~^\s*'.implode('\s+',$pieces).'\s*$~iD';
        if(!preg_match($pattern,$norm((string)($observed['command']??''))))return false;
        foreach(self::portsOf($spec) as $port){
            if(($ports[$port]??[])!==[$pid])return false;
        }
        return true;
    }
    private function observations():array
    {
        $processes=self::index(($this->inventory)());
        $ports=($this->listeners)();
        foreach($this->managedSpecs as $spec){
            foreach(self::portsOf($spec) as $port){
                if(($ports[$port]??[])!==[])continue;
                $owner=($this->activeOwner)($port);
                if(is_int($owner) && $owner>0 && isset($processes[$owner]))$ports[$port]=[$owner];
            }
        }
        return [$processes,$ports];
    }
    public function status():array
    {
        $this->assertNoPending();
        [$processes,$ports]=$this->observations();$stored=$this->records();$result=[];
        foreach($this->managedSpecs as $name=>$spec){
            $rec=$stored[$name]??null;
            if (is_array($rec) && isset($processes[$rec['pid']??0]) && self::attest($rec,$spec,$processes[$rec['pid']],$ports)) {
                $result[$name]='ATTESTED';
            } elseif (self::occupied($spec,$ports)) {
                $result[$name]='PORT_UNVERIFIED';
            } elseif (is_array($rec) && isset($processes[$rec['pid']??0])) {
                $result[$name]='RECORDED_UNVERIFIED';
            } else {
                // Une attestation historique sans PID ni port ne signifie pas processus actif.
                // La mutation de cette preuve ne se fera que sous verrou et double constat.
                $result[$name]='ABSENT';
            }
        }
        return $result;
    }

    /**
     * Réconcilie uniquement les preuves dont le PID est absent et le port libre.
     * Une réutilisation de PID, une identité incertaine ou un port occupé bloque.
     * Appeler exclusivement sous native-lifecycle.lock.
     */
    private static function occupied(array $spec,array $ports):bool
    {
        foreach(self::portsOf($spec) as $port)if(($ports[$port]??[])!==[])return true;
        return false;
    }
    private function reconcileDeadRecords(array &$stored, array $processes, array $ports, ?array $only=null):void
    {
        $dead=[];
        foreach($stored as $name=>$record){
            if(!isset($this->managedSpecs[$name]) || !is_array($record))
                throw new \RuntimeException('EZS_NATIVE_UNKNOWN_RECORD');
            if($only!==null && !in_array($name,$only,true))continue;
            $pid=(int)($record['pid']??0);
            if($pid<1)throw new \RuntimeException('EZS_NATIVE_INVALID_RECORDED_PID');
            if(isset($processes[$pid])){
                if(!self::attest($record,$this->managedSpecs[$name],$processes[$pid],$ports))
                    throw new \RuntimeException('EZS_NATIVE_IDENTITY_UNVERIFIED_'.$name);
                continue;
            }
            if(self::occupied($this->managedSpecs[$name],$ports))
                throw new \RuntimeException('EZS_NATIVE_STALE_PORT_OCCUPIED_'.$name);
            $dead[$name]=$pid;
        }
        if($dead===[])return;
        usleep(200000);
        [$again,$portsAgain]=$this->observations();
        foreach($dead as $name=>$pid){
            if(isset($again[$pid]) || self::occupied($this->managedSpecs[$name],$portsAgain))
                throw new \RuntimeException('EZS_NATIVE_STALE_RACE_'.$name);
        }
        // Ne jamais supprimer les preuves : conserver un journal durable.
        $journal=$this->runtime.'/native-reconciled.log';
        foreach($dead as $name=>$pid){
            $line=gmdate('c').' DEAD_RECORD '.$name.' PID='.$pid."\n";
            if(file_put_contents($journal,$line,FILE_APPEND|LOCK_EX)===false)
                throw new \RuntimeException('EZS_NATIVE_RECONCILIATION_LOG_FAILED');
        }
        foreach($dead as $name=>$_pid)unset($stored[$name]);
        $this->persist($stored);
    }
    private function reconcileLegacy():void
    {
        if($this->profile==='prod')return; // runtime PROD historique = autre format, jamais muté ici.
        [$processes,$ports]=$this->observations();
        foreach (['processes.json'=>['php_pid','caddy_pid'],
                  'app-backends.json'=>['dev_pid','preview_pid'],
                  'lab-assistant.json'=>['lab.pid','assistant.pid']] as $file=>$keys) {
            $path=$this->runtime.'/'.$file;
            if(!is_file($path)) continue;
            $state=json_decode((string)file_get_contents($path),true,512,JSON_THROW_ON_ERROR);
            if(!is_array($state))throw new \RuntimeException('EZS_NATIVE_LEGACY_STATE_INVALID_'.$file);
            foreach($keys as $key) {
                $v=$state;
                foreach(explode('.',$key) as $part){$v=is_array($v)?($v[$part]??null):null;}
                if(!is_numeric($v) || (int)$v<1)throw new \RuntimeException('EZS_NATIVE_LEGACY_PID_INVALID_'.$file);
                if(isset($processes[(int)$v]))throw new \RuntimeException('EZS_NATIVE_LEGACY_PID_ACTIVE_'.$v);
            }
            foreach($this->managedSpecs as $spec){if(self::occupied($spec,$ports))throw new \RuntimeException('EZS_NATIVE_LEGACY_LISTENER_ACTIVE_'.$spec['port']);}
            throw new \RuntimeException('EZS_NATIVE_LEGACY_REQUIRES_MANUAL_RECONCILIATION_'.$file);
        }
    }
    public function start():array
    {
        return $this->withLock(function():array{
            $this->reconcilePending();
            $this->reconcileLegacy();
            $stored=$this->records();[$processes,$ports]=$this->observations();
            $this->reconcileDeadRecords($stored,$processes,$ports);
            [$processes,$ports]=$this->observations();
            // Un état encore vivant mais non attesté ne peut être adopté ou remplacé.
            foreach($this->managedSpecs as $name=>$spec){
                $rec=$stored[$name]??null;
                if($rec!==null && (!is_array($rec) || !isset($processes[$rec['pid']??0]) ||
                   !self::attest($rec,$spec,$processes[$rec['pid']],$ports)))
                   throw new \RuntimeException('EZS_NATIVE_START_REFUSED_STATE_'.$name);
                if($rec===null && self::occupied($spec,$ports))
                   throw new \RuntimeException('EZS_NATIVE_START_REFUSED_PORT_'.$name);
            }
            // Préflight global : aucune création si une dépendance manque.
            foreach($this->managedSpecs as $name=>$spec){
                if(isset($stored[$name]))continue;
                if(!(($this->dependencyAvailable)($spec['exe'],$spec['cwd'])))
                    throw new \RuntimeException('EZS_NATIVE_DEPENDENCY_MISSING_'.$name);
            }
            $new=[];
            foreach($this->managedSpecs as $name=>$spec){
                if(isset($stored[$name]))continue;
                $this->pending($name);
                $pid=($this->spawn)($spec['exe'],$spec['args'],$spec['cwd']);
                if(!is_int($pid) || $pid<1)throw new \RuntimeException('EZS_NATIVE_CREATE_FAILED_'.$name);
                $attested=false;
                for($i=0;$i<60;$i++){
                    usleep(250000);
                    [$processes,$ports]=$this->observations();
                    $p=$processes[$pid]??null;
                    if($p===null)continue;
                    $rec=['pid'=>$pid,'created'=>(string)($p['created']??'')];
                    if(self::attest($rec,$spec,$p,$ports)){$stored[$name]=$rec;$new[$name]=$pid;$this->persist($stored);$this->clearPending();$attested=true;break;}
                }
                if(!$attested)throw new \RuntimeException('EZS_NATIVE_START_UNATTESTED_'.$name.'_PID_'.$pid);
            }
            return $new;
        });
    }
    public function stop():array
    {
        return $this->withLock(function():array{
            $this->assertNoPending();
            $stored=$this->records();[$processes,$ports]=$this->observations();
            foreach($stored as $name=>$rec){
                if(!isset($this->managedSpecs[$name]) || !is_array($rec) || !isset($processes[$rec['pid']??0]) ||
                   !self::attest($rec,$this->managedSpecs[$name],$processes[$rec['pid']],$ports))
                    throw new \RuntimeException('EZS_NATIVE_STOP_REFUSED_UNVERIFIED_'.$name);
            }
            $stopped=[];
            foreach(array_reverse(array_keys($this->managedSpecs)) as $name){
                if(!isset($stored[$name]))continue;
                $rec=$stored[$name];$pid=(int)$rec['pid'];
                // Attestation renouvelée immédiatement avant toute terminaison.
                [$processes,$ports]=$this->observations();
                if(!isset($processes[$pid]) || !self::attest($rec,$this->managedSpecs[$name],$processes[$pid],$ports))
                    throw new \RuntimeException('EZS_NATIVE_STOP_IDENTITY_CHANGED_'.$name);
                if(!($this->terminate)($pid))throw new \RuntimeException('EZS_NATIVE_STOP_FAILED_'.$name);
                $gone=false;
                for($i=0;$i<40;$i++){
                    usleep(250000);[$processes,$ports]=$this->observations();
                    if(!isset($processes[$pid]) && !self::occupied($this->managedSpecs[$name],$ports)){$gone=true;break;}
                }
                if(!$gone)throw new \RuntimeException('EZS_NATIVE_STOP_NOT_EXITED_'.$name);
                unset($stored[$name]);$this->persist($stored);$stopped[$name]=$pid;
            }
            return $stopped;
        });
    }
    /** Groupes commandables séparément ; aucun groupe ne contient les processus racine de l'interface. */
    public static function groups(): array
    {
        return [
            'dev' => ['ezscore_dev', 'ezscore_preview'],
            'lab' => ['lab'],
            'assistant' => ['assistant'],
        ];
    }

    /** @return list<string> */
    private function groupNames(string $group): array
    {
        $groups = $this->profile==='prod' ? ['prod'=>array_keys(self::PROD)] :
            ['root'=>['root_php','root_caddy'],...self::groups()];
        if (!isset($groups[$group])) {
            throw new \InvalidArgumentException('EZS_NATIVE_GROUP_REFUSED');
        }
        return $groups[$group];
    }

    /** Démarre exclusivement le groupe demandé, en conservant les preuves des autres groupes. */
    public function startGroup(string $group): array
    {
        $names = $this->groupNames($group);
        return $this->withLock(function () use ($names): array {
            $this->reconcilePending();
            $this->reconcileLegacy();
            $stored = $this->records();
            [$processes, $ports] = $this->observations();
            $this->reconcileDeadRecords($stored,$processes,$ports);
            [$processes, $ports] = $this->observations();
            foreach ($stored as $name => $record) {
                if (!isset($this->managedSpecs[$name]) || !is_array($record)) {
                    throw new \RuntimeException('EZS_NATIVE_UNKNOWN_RECORD');
                }
                if(!in_array($name,$names,true))continue;
                $pid = (int)($record['pid'] ?? 0);
                if ($pid < 1 || !isset($processes[$pid]) ||
                    !self::attest($record, $this->managedSpecs[$name], $processes[$pid], $ports)) {
                    throw new \RuntimeException('EZS_NATIVE_GROUP_START_REFUSED_STATE_'.$name);
                }
            }
            // Refus de toute occupation non attribuée, y compris sur un autre groupe.
            foreach ($names as $name) {
                $spec=$this->managedSpecs[$name];
                if (!isset($stored[$name]) && self::occupied($spec,$ports)) {
                    throw new \RuntimeException('EZS_NATIVE_GROUP_START_REFUSED_PORT_'.$name);
                }
            }
            foreach ($names as $name) {
                if (!isset($stored[$name]) && !(($this->dependencyAvailable)($this->managedSpecs[$name]['exe'], $this->managedSpecs[$name]['cwd']))) {
                    throw new \RuntimeException('EZS_NATIVE_DEPENDENCY_MISSING_'.$name);
                }
            }
            $started = [];
            foreach ($names as $name) {
                if (isset($stored[$name])) continue;
                $spec = $this->managedSpecs[$name];
                $this->pending($name);
                $pid = ($this->spawn)($spec['exe'], $spec['args'], $spec['cwd']);
                if (!is_int($pid) || $pid < 1) throw new \RuntimeException('EZS_NATIVE_CREATE_FAILED_'.$name);
                $attested = false;
                for ($i = 0; $i < 60; $i++) {
                    usleep(250000);
                    [$processes, $ports] = $this->observations();
                    $observed = $processes[$pid] ?? null;
                    if ($observed === null) continue;
                    $record = ['pid' => $pid, 'created' => (string)($observed['created'] ?? '')];
                    if (self::attest($record, $spec, $observed, $ports)) {
                        $stored[$name] = $record;
                        $started[$name] = $pid;
                        $this->persist($stored);
                        $this->clearPending();
                        $attested = true;
                        break;
                    }
                }
                if (!$attested) throw new \RuntimeException('EZS_NATIVE_START_UNATTESTED_'.$name.'_PID_'.$pid);
            }
            return $started;
        });
    }

    /** Arrête exclusivement le groupe demandé, jamais root_php/root_caddy ni l'IA. */
    public function stopGroup(string $group): array
    {
        $names = $this->groupNames($group);
        return $this->withLock(function () use ($names): array {
            $this->assertNoPending();
            $stored = $this->records();
            [$processes, $ports] = $this->observations();
            foreach ($stored as $name => $record) {
                if(!in_array($name,$names,true))continue;
                $pid = is_array($record) ? (int)($record['pid'] ?? 0) : 0;
                if (!isset($this->managedSpecs[$name]) || $pid < 1 || !isset($processes[$pid]) ||
                    !self::attest($record, $this->managedSpecs[$name], $processes[$pid], $ports)) {
                    throw new \RuntimeException('EZS_NATIVE_GROUP_STOP_REFUSED_UNVERIFIED_'.$name);
                }
            }
            $stopped = [];
            foreach (array_reverse($names) as $name) {
                if (!isset($stored[$name])) continue;
                $record = $stored[$name];
                $pid = (int)$record['pid'];
                [$processes, $ports] = $this->observations();
                if (!isset($processes[$pid]) ||
                    !self::attest($record, $this->managedSpecs[$name], $processes[$pid], $ports)) {
                    throw new \RuntimeException('EZS_NATIVE_GROUP_STOP_IDENTITY_CHANGED_'.$name);
                }
                if (!(($this->terminate)($pid))) throw new \RuntimeException('EZS_NATIVE_GROUP_STOP_FAILED_'.$name);
                $gone = false;
                for ($i = 0; $i < 40; $i++) {
                    usleep(250000);
                    [$processes, $ports] = $this->observations();
                    if (!isset($processes[$pid]) && !self::occupied($this->managedSpecs[$name],$ports)) {
                        $gone = true;
                        break;
                    }
                }
                if (!$gone) throw new \RuntimeException('EZS_NATIVE_GROUP_STOP_NOT_EXITED_'.$name);
                unset($stored[$name]);
                $this->persist($stored);
                $stopped[$name] = $pid;
            }
            return $stopped;
        });
    }

    private static function wmi():object
    {
        if(PHP_OS_FAMILY!=='Windows' || !class_exists('COM'))throw new \RuntimeException('EZS_NATIVE_WMI_UNAVAILABLE');
        return (new \COM('WbemScripting.SWbemLocator'))->ConnectServer('.','root\\cimv2');
    }
    private static function nativeSpawn(string $exe,string $args,string $cwd):int
    {
        // Exécutable et arguments séparés : pas de cmd.exe, pas de PowerShell.
        // Les deux formes d'arguments actuellement utilisées sont :
        //   -b 127.0.0.1:PORT
        //   run --config "CHEMIN" --adapter caddyfile
        $tokens = self::spawnArguments($args);
        $command = array_merge([$exe], $tokens);
        // stdout/stderr de serveurs persistants : journaux durables, jamais dans H:/temp.
        // Les anciens fichiers déjà ouverts ne sont ni déplacés ni supprimés.
        $logDir = self::ROOT.'/var/log/native';
        if (!is_dir($logDir) && !mkdir($logDir, 0700, true) && !is_dir($logDir))
            throw new \RuntimeException('EZS_PROC_LOG_DIR_FAILED');
        if (!is_writable($logDir))
            throw new \RuntimeException('EZS_PROC_LOG_DIR_NOT_WRITABLE');
        $name = bin2hex(random_bytes(8));
        $descriptors = [
            0 => ['file', 'NUL', 'r'],
            1 => ['file', $logDir.'/'. $name .'.out.log', 'a'],
            2 => ['file', $logDir.'/'. $name .'.err.log', 'a'],
        ];
        $env=null;
        if(strcasecmp(str_replace('\\','/',$cwd),'H:/EZScore')===0){
            $env=getenv();
            if(!is_array($env))$env=[];
            $env['APP_ENV']='prod';
            $env['APP_DEBUG']='0';
            $env['EZSCORE_INSTANCE']='prod';
        } elseif(strcasecmp(str_replace('\\','/',$cwd),self::ROOT.'/runtime_components/prod_gateway_php')===0){
            $env=getenv();
            if(!is_array($env))$env=[];
            $env['EZS_GATEWAY_RECIPE_CONFIG']='';
            $env['EZS_GATEWAY_RECIPE_MODE']='';
        }
        $resource = proc_open($command, $descriptors, $pipes, $cwd, $env, [
            'bypass_shell' => true,
            'create_new_console' => false,
            'suppress_errors' => true,
        ]);
        if (!is_resource($resource)) throw new \RuntimeException('EZS_PROC_CREATE_FAILED');
        $status = proc_get_status($resource);
        $pid = (int)($status['pid'] ?? 0);
        if ($pid <= 0 || !($status['running'] ?? false)) {
            proc_close($resource);
            throw new \RuntimeException('EZS_PROC_EXITED_BEFORE_ATTESTATION');
        }
        // Ne pas appeler proc_close() : il attendrait la fin du serveur.
        // Les descripteurs sont des fichiers et non des pipes ; le moteur
        // conserve l'attestation WMI + TCP et l'état persistant existants.
        self::$spawnHandles[] = $resource;
        return $pid;
    }

    /** @return list<string> */
    public static function spawnArguments(string $args):array
    {
        if (preg_match('~^-b (127\.0\.0\.1:[0-9]{1,5})$~D', $args, $m))
            return ['-b', $m[1]];
        if (preg_match('~^run --config "([^"]+)" --adapter caddyfile$~D', $args, $m))
            return ['run', '--config', $m[1], '--adapter', 'caddyfile'];
        throw new \InvalidArgumentException('EZS_PROC_ARGS_REFUSED');
    }

    private static function nativeTerminate(int $pid):bool
    {
        $service=self::wmi();
        $process=$service->Get('Win32_Process.Handle="'.$pid.'"');
        return (int)$process->Terminate(0)===0;
    }
    private static function nativeListeners():array
    {
        // netstat est un utilitaire natif en lecture seule ; aucun shell PowerShell.
        $p=new \Symfony\Component\Process\Process(['C:/Windows/System32/netstat.exe','-ano','-p','tcp']);
        $p->run();if(!$p->isSuccessful())throw new \RuntimeException('EZS_NATIVE_NETSTAT_FAILED');
        $all=WindowsPortOwnership::parseListeners($p->getOutput());
        foreach($all as &$list){sort($list,SORT_NUMERIC);}unset($list);
        return $all;
    }
}
