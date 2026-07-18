/**
 * Electron main process for Sayanjali Nexus CRM.
 *
 * Dev mode: loads the Vite dev server (http://localhost:5173) and expects
 * the FastAPI backend to already be running separately (`uvicorn ... --reload`).
 *
 * Packaged mode: spawns the bundled Python backend as a child process on
 * app startup and points the window at the built frontend files.
 */
const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

const isDev = !app.isPackaged;
let backendProcess = null;
let mainWindow = null;

function startBackend() {
  if (isDev) return; // assume `uvicorn --reload` is already running in dev

  const backendExe = path.join(process.resourcesPath, "backend", "sayanjali-crm-backend");
  backendProcess = spawn(backendExe, [], { cwd: path.dirname(backendExe) });
  backendProcess.stdout.on("data", (d) => console.log(`[backend] ${d}`));
  backendProcess.stderr.on("data", (d) => console.error(`[backend] ${d}`));
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    backgroundColor: "#12131A",
    title: "Sayanjali Nexus CRM",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
    mainWindow.webContents.openDevTools({ mode: "detach" });
  } else {
    mainWindow.loadFile(path.join(__dirname, "../frontend/dist/index.html"));
  }
}

app.whenReady().then(() => {
  startBackend();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (backendProcess) backendProcess.kill();
  if (process.platform !== "darwin") app.quit();
});
