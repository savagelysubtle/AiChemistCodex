
export const TEST_CASES = {
  resources: [
    {
      name: 'Current Directory Resource',
      uri: 'cli://currentdir',
      expectedMimeType: 'text/plain'
    },
    {
      name: 'Config Resource',
      uri: 'cli://config',
      expectedMimeType: 'application/json'
    },
    {
      name: 'History Resource',
      uri: 'cli://history',
      expectedMimeType: 'application/json'
    }
  ],

  commands: [
    {
      name: 'Basic Command',
      input: {
        shell: 'powershell',
        command: 'Get-Date'
      },
      expectedExitCode: 0
    },
    {
      name: 'Unix Translation',
      input: {
        shell: 'cmd',
        command: 'ls -la'
      },
      expectedTranslation: 'dir /a'
    },
    {
      name: 'Destructive Command Without Force',
      input: {
        shell: 'powershell',
        command: 'Remove-Item test.txt'
      },
      expectsError: true,
      errorPattern: /potentially destructive.*requires.*force/
    },
    {
      name: 'Dry Run Test',
      input: {
        shell: 'cmd',
        command: 'echo "test"',
        dryRun: true
      },
      expectsDryRun: true
    }
  ],

  timeouts: [
    {
      name: 'Command Timeout',
      input: {
        shell: 'powershell',
        command: 'Start-Sleep -Seconds 400' // Longer than default timeout
      },
      expectsTimeout: true
    }
  ],

  streaming: [
    {
      name: 'Large Output Streaming',
      input: {
        shell: 'powershell',
        command: 'Get-Process | Format-List *'
      },
      expectsStreamingUpdates: true
    }
  ],

  interrupts: [
    {
      name: 'SIGINT Handling',
      input: {
        shell: 'powershell',
        command: 'Start-Sleep -Seconds 30'
      },
      testInterrupt: true
    }
  ]
};