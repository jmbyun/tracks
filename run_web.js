const { spawn } = require('child_process');
const path = require('path');

/**
 * Run the Web application (Vite) development server.
 */
function main() {
    console.log('Starting Web application server (tracks-web)...');

    // Launch 'npm run dev' inside the tracks-web directory
    const child = spawn('npm', ['run', 'dev'], {
        cwd: path.join(__dirname, 'tracks-web'),
        stdio: 'inherit',
        shell: true
    });

    child.on('error', (err) => {
        console.error('Failed to start web server:', err);
        process.exit(1);
    });

    // Handle process signals to ensure child is cleaned up if needed
    // (Though 'inherit' usually handles this well with npm)
    process.on('SIGINT', () => {
        child.kill('SIGINT');
        process.exit();
    });
}

main();
