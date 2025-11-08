module.exports = {
  apps: [
    {
      name: "seagri",
      script: "server.js",
      cwd: "/var/www/virdia.com.br/html/seagri",
      env: {
        NODE_ENV: "production",
        PORT: 3040
      },
      instances: 1,
      exec_mode: "fork",
      max_memory_restart: "1G"
    }
  ]
}
