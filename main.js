const {
    app,
    BrowserWindow,
    ipcMain
} = require('electron');
const path = require('path');
const yargs = require('yargs');
const fs = require('fs');
const asar = require('asar');

const argv = yargs
    .positional('file', {
        alias: 'f',
        describe: 'markdown file to load',
        type: 'string',
        default: "",
    })
    .positional('tmpl', {
        alias: 't',
        describe: 'template index.html',
        type: 'string',
        default: "",
    })
    .option('width', {
        alias: 'w',
        describe: 'window width',
        type: 'number',
        default: '800'
    })
    .option('height', {
        alias: 'h',
        describe: 'window height',
        type: 'number',
        default: '600'
    })
    .option('x', {
        alias: 'x',
        describe: 'window x position',
        type: 'number',
        default: '0'
    })
    .option('y', {
        alias: 'y',
        describe: 'window y position',
        type: 'number',
        default: '0'
    })
    .argv;

function createWindow(file) {
    const mainWindow = new BrowserWindow({
        width: argv.width,
        height: argv.height,
        x: argv.x,
        y: argv.y,
        webPreferences: {
            nodeIntegration: true
        }
    });

    mainWindow.loadURL(file);

    ipcMain.on('updateContent', (event, content) => {
        mainWindow.webContents.send('updateContent', content);

    });
}

const defaultTmpl = `
    <!doctype html>
    <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>slidev</title>
            <link rel="stylesheet" href="dist/reset.css">
            <link rel="stylesheet" href="dist/reveal.css">
            <link rel="stylesheet" href="dist/theme/black.css">
            <link rel="stylesheet" href="plugin/highlight/monokai.css">
        </head>
        <body>
            <div class="reveal">
                <div class="slides">
                    <section data-markdown data-separator="^---" data-separator-vertical="^--">
                        <textarea data-template>
                            {{markdownContent}}
                        </textarea>
                    </section>
                </div>
            </div>
            <script src="dist/reveal.js"></script>
            <script src="plugin/notes/notes.js"></script>
            <script src="plugin/markdown/markdown.js"></script>
            <script src="plugin/highlight/highlight.js"></script>
            <script>
                Reveal.initialize({
                    hash: true,
                    plugins: [ RevealMarkdown, RevealHighlight, RevealNotes ]
                });
            </script>
        </body>
    </html>
`;


function generateHTMLFromMarkdown(markdownFile, outputPath) {
    try {
        let markdownContent = fs.readFileSync(markdownFile, 'utf8');

        let tmpl = defaultTmpl

        if (argv.tmpl !== "") {
            tmpl = fs.readFileSync(path.resolve(argv.tmpl), 'utf8');
        }

        let htmlString = tmpl.replace('{{markdownContent}}', markdownContent);

        fs.writeFileSync(outputPath, htmlString);
    } catch (error) {
        console.error('Error generating HTML file:', error);
    }
}

app.whenReady().then(() => {
    const flagRegex = /^-{1,2}\w+$/;
    const file = process.argv[1]

    const asarFilePath = app.getAppPath()
    const cachePath = app.getPath('cache');
    const unpackedDir = path.join(cachePath, app.name, 'unpacked');

    if (file && !flagRegex.test(file)) {
        if (!fs.existsSync(unpackedDir)) {
            try {
                asar.extractAll(asarFilePath, unpackedDir);
                console.log('Extraction successful.');
            } catch (error) {
                console.error('Extraction failed:', error);
                return;
            }
        }
        generateHTMLFromMarkdown(path.resolve(file), path.join(unpackedDir, "reveal.js/index.html"))
        createWindow(`file://${path.join(unpackedDir, "reveal.js/index.html")}`);
    } else {
        console.log('no files.');
        app.quit()
    }

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
