module.exports = {
  apps: [{
    name: 'RGNODES-VPS-BOT',
    cwd: '/root/rgnodes-vps-bot',
    script: 'bot.py',
    interpreter: '/root/rgnodes-vps-bot/.venv/bin/python',
    interpreter_args: '-u',
    exec_mode: 'fork',
    instances: 1,
    autorestart: true,
    restart_delay: 5000,
    exp_backoff_restart_delay: 100,
    max_memory_restart: '768M',
    kill_timeout: 15000,
    listen_timeout: 15000,
    merge_logs: true,
    env: { PYTHONUNBUFFERED: '1' }
  }]
};
