param(
    [Parameter(Mandatory = $true)]
    [string]$ReadyFile,
    [Parameter(Mandatory = $true)]
    [string]$FailureFile,
    [int]$TimeoutSeconds = 20
)

$ErrorActionPreference = "SilentlyContinue"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
$form.Width = 520
$form.Height = 260
$form.BackColor = [System.Drawing.Color]::FromArgb(10, 16, 19)
$form.TopMost = $true
$form.ShowInTaskbar = $false

$border = New-Object System.Windows.Forms.Panel
$border.Dock = [System.Windows.Forms.DockStyle]::Fill
$border.Padding = New-Object System.Windows.Forms.Padding(2)
$border.BackColor = [System.Drawing.Color]::FromArgb(73, 209, 189)
$form.Controls.Add($border)

$body = New-Object System.Windows.Forms.Panel
$body.Dock = [System.Windows.Forms.DockStyle]::Fill
$body.BackColor = [System.Drawing.Color]::FromArgb(16, 25, 30)
$border.Controls.Add($body)

$logo = New-Object System.Windows.Forms.Label
$logo.Text = "EZ"
$logo.AutoSize = $false
$logo.Width = 74
$logo.Height = 74
$logo.Left = 34
$logo.Top = 50
$logo.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$logo.Font = New-Object System.Drawing.Font("Segoe UI", 24, [System.Drawing.FontStyle]::Bold)
$logo.ForeColor = [System.Drawing.Color]::FromArgb(73, 209, 189)
$logo.BackColor = [System.Drawing.Color]::FromArgb(23, 59, 55)
$body.Controls.Add($logo)

$title = New-Object System.Windows.Forms.Label
$title.Text = "EZS ORCHESTRATOR"
$title.AutoSize = $true
$title.Left = 132
$title.Top = 58
$title.Font = New-Object System.Drawing.Font("Segoe UI", 19, [System.Drawing.FontStyle]::Bold)
$title.ForeColor = [System.Drawing.Color]::FromArgb(237, 245, 244)
$body.Controls.Add($title)

$version = New-Object System.Windows.Forms.Label
$version.Text = "V1.0"
$version.AutoSize = $true
$version.Left = 135
$version.Top = 96
$version.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$version.ForeColor = [System.Drawing.Color]::FromArgb(145, 166, 172)
$body.Controls.Add($version)

$status = New-Object System.Windows.Forms.Label
$status.Text = "Démarrage du Control Center…"
$status.AutoSize = $false
$status.Width = 440
$status.Height = 26
$status.Left = 35
$status.Top = 158
$status.TextAlign = [System.Drawing.ContentAlignment]::MiddleLeft
$status.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$status.ForeColor = [System.Drawing.Color]::FromArgb(203, 216, 218)
$body.Controls.Add($status)

$progress = New-Object System.Windows.Forms.ProgressBar
$progress.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
$progress.Minimum = 0
$progress.Maximum = 100
$progress.Value = 4
$progress.Left = 35
$progress.Top = 194
$progress.Width = 440
$progress.Height = 12
$body.Controls.Add($progress)

$started = [DateTime]::UtcNow
$progressValue = 4

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 120
$timer.Add_Tick({
    if (Test-Path -LiteralPath $ReadyFile) {
        $progress.Value = 100
        $status.Text = "Control Center prêt"
        $timer.Stop()

        $closeTimer = New-Object System.Windows.Forms.Timer
        $closeTimer.Interval = 220
        $closeTimer.Add_Tick({
            $closeTimer.Stop()
            $form.Close()
        })
        $closeTimer.Start()
        return
    }

    if (Test-Path -LiteralPath $FailureFile) {
        $status.Text = "Échec du démarrage — voir control-center-error.log"
        $status.ForeColor = [System.Drawing.Color]::FromArgb(255, 123, 123)
        $progress.Value = 100

        $closeTimer = New-Object System.Windows.Forms.Timer
        $closeTimer.Interval = 2500
        $closeTimer.Add_Tick({
            $closeTimer.Stop()
            $form.Close()
        })
        $closeTimer.Start()
        $timer.Stop()
        return
    }

    # Visible deterministic progress while the launcher validates the service
    # and the Control Center listener. It deliberately stops at 92% until
    # ReadyFile confirms the listener is really ours.
    if ($progressValue -lt 92) {
        if ($progressValue -lt 35) {
            $progressValue += 3
        }
        elseif ($progressValue -lt 70) {
            $progressValue += 2
        }
        else {
            $progressValue += 1
        }
        if ($progressValue -gt 92) {
            $progressValue = 92
        }
        $progress.Value = $progressValue
    }

    $elapsed = ([DateTime]::UtcNow - $started).TotalSeconds
    if ($elapsed -ge $TimeoutSeconds) {
        $status.Text = "Démarrage plus long que prévu…"
    }
    elseif ($progressValue -ge 70) {
        $status.Text = "Vérification du Control Center…"
    }
    elseif ($progressValue -ge 35) {
        $status.Text = "Initialisation des services…"
    }
})
$timer.Start()

[void]$form.ShowDialog()
