const express = require('express');
const app = express();
const router = express.Router();
const path = require('path');
const marked = require('marked');
const fs = require('fs');

app.use('/', router);
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(__dirname +  '/out'));
app.use('/docs', express.static(__dirname + '/docs'));
app.use('/cards', express.static(__dirname +  '/cards'));
app.use(express.static(__dirname + '/site'));


router.get('/', (req, res) => {
    res.sendFile(__dirname + '/site/index.html');
});

app.get('/creator', (req, res) => {
    res.sendFile(__dirname + '/site/creator.html');
});

app.post('/create', (req, res) => {
    const { spawn } = require('child_process');

    if (fs.existsSync(__dirname + '/tmp/cards.txt')) {
        try {
            fs.mkdirSync(__dirname + '/tmp/_archive');
        } catch (e) {
            if (e.code !== 'EEXIST') {
                console.log('Cannot create directory', e);
                return res.end();
            }
        }

        fs.renameSync(__dirname + '/tmp/cards.txt', __dirname + '/tmp/_archive/cards_' + (new Date()).toISOString() + '.txt');
    }

    try {
        fs.mkdirSync(__dirname + '/tmp');
    } catch (e) {
        if (e.code !== 'EEXIST') {
            console.log('Cannot create directory', e);
            return res.end();
        }
    }

    try {
        fs.writeFileSync(__dirname + '/tmp/cards.txt', req.body.commands);
    } catch (e){
        console.log('Cannot write file', e);
        return res.end();
    }

    var args = [
        './qrgen.py',
        '--input=tmp/cards.txt'
    ];

    if (req.body.printmode === 'dublex') {
        args.push('--print-dublex');
    }

    const pyProg = spawn('python3', args);

    pyProg.stdout.on('close', function(data) {
        res.redirect('/result');
    });
});

app.get('/result', (req, res) => {
    res.sendFile(__dirname + '/out/index.html');
});

app.get('/readme', (req, res) => {
    fs.readFile(path.join(__dirname, 'README.md'), 'utf8', function(err, data) {
        if(err) {
            console.log(err);
        }
        res.send(marked(data.toString()));
    });
});

app.get('/license', (req, res) => {
    fs.readFile(path.join(__dirname, 'LICENSE'), function (err, data) {
        if (err) {
            throw err;
        }
        res.writeHead(200, {'Content-Type': 'text/html'});
        res.write('<pre>');
        res.write(data);
        res.write('</pre>');
        res.end();
    });
});

app.listen(5006, () => console.log('Application listening on port 5006!'))