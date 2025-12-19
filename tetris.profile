# Firejail profile for sandboxing Tetris bot executions
# This profile restricts filesystem access, drops capabilities, limits resources, and prevents network access
# while allowing stdin/stdout communication for bot interaction

# Include common disable directives to block common attack vectors
include /etc/firejail/disable-common.inc

# Drop all Linux capabilities to prevent privilege escalation
caps.drop all

# Disable all network access to prevent data exfiltration or external communication
net none

# Limit address space to 1GB to prevent memory exhaustion attacks
rlimit-as 1000000000

# Limit CPU time to 10 seconds to prevent infinite loops or resource hogging
rlimit-cpu 10

# Restrict filesystem access by blacklisting sensitive directories
blacklist /home
blacklist /tmp
blacklist /var
blacklist /usr/local
blacklist /opt

# Whitelist the current working directory to allow access to bot code and necessary files
whitelist /home/william/INSAlgo/Concours-Tetris

# Allow stdin/stdout/stderr for bot interaction (default behavior, but ensured by not redirecting)
# No additional directives needed as Firejail preserves standard I/O by default