const {
    lstatSync,
    readdirSync,
    statSync
} = require('fs');
const fs = require('fs');
const rimraf = require("rimraf");
const pngquant = require('pngquant-bin');
const {join} = require('path');
const execFileSync = require('child_process').execFileSync;
const mozjpeg = require('mozjpeg');
const _cliProgress = require('cli-progress');
const bar1 = new _cliProgress.SingleBar({}, _cliProgress.Presets.shades_classic);

const PATH_DIRECT = '/home/maksimov/Documents/testconvert/nodescript/';
const bufferDir = '/tmp/buffer'

const isDirectory = source => lstatSync(source).isDirectory();
const getDirectories = source =>
    readdirSync(source).map(name => join(source, name)).filter(isDirectory);
let listDirectories = getDirectories(PATH_DIRECT);
let extention_f;
const path_uploads = 'uploads'


const logdir = 'log';
if (!fs.existsSync(logdir)) {
    fs.mkdirSync(logdir);
}
if (!fs.existsSync(bufferDir)) {
    fs.mkdirSync(bufferDir);
}

let set_compress_dir = new Set();

if (fs.existsSync(join(logdir, 'compress-dir.txt'))) {
    fs.readFileSync(join(logdir, 'compress-dir.txt'), 'utf-8').split(/\r?\n/).forEach(line => {
        set_compress_dir.add(line);
    })
}

function getExtensionFile(path) {
    return path.match(/[a-zA-Z]+$/i);
}

function getNameFile(path) {
    return path.split('/').slice(-1)[0]
}

console.log("Директорий пройдено : %s", set_compress_dir.size)
const resume_dirs = listDirectories.filter(path_file =>
    !set_compress_dir.has(path_file));
console.log("Осталось пройти : %s", resume_dirs.length)

function checkFileDirJpeg(listBiggerFile1mb, imageDir) { //  возвращает список файлов из всех каталогов
    let stats, filePath;
    fs.readdirSync(imageDir).forEach(file => {
        filePath = join(imageDir, file);
        stats = statSync(filePath);
        if (stats.isFile()) {
            extention_f = getExtensionFile(file)
            if (extention_f == 'jpg' || extention_f == 'jpeg') {
                if (stats.size / 1000000.0 > 0.2) {
                    listBiggerFile1mb.push(filePath);

                }
            }
        } else {
            checkFileDirJpeg(listBiggerFile1mb, join(imageDir, file))
        }
    });
}



for (let i = 0; i < resume_dirs.length; i++) {
    let listBiggerFile1mb = [];
    console.log('Директория %s из %s : name: %s', i + 1, resume_dirs.length, resume_dirs[i])
    let imageDir = join(resume_dirs[i], path_uploads);

    if (fs.existsSync(imageDir)) {
        checkFileDirJpeg(listBiggerFile1mb, imageDir)

    } else continue

    let set_compress_file = new Set();
    let siteName = join(logdir, getNameFile(resume_dirs[i])) + '.txt';
    if (fs.existsSync(siteName)) {
        fs.readFileSync(siteName, 'utf-8').split(/\r?\n/).forEach(line => {
            set_compress_file.add(line);
        });
    }

    const newListFiles = listBiggerFile1mb.filter(path_file =>
        !set_compress_file.has(path_file));
    let wasSize = 0
    let nowSize = 0
    let nameFileInBuffer;
    bar1.start(newListFiles.length, 0);
    for (let i = 0; i < newListFiles.length; i++) {
        try {
            nameFileInBuffer = join(bufferDir, getNameFile(newListFiles[i]))

            let timeModif = statSync(newListFiles[i]).mtime
            // Перемещае файл в буфер
            fs.renameSync(newListFiles[i], nameFileInBuffer, function (err) {
                if (err) {
                    console.log('Ошибка при переносе в буфер')
                    throw err
                }
            });
            let sizeFile = statSync(nameFileInBuffer).size


            let sizeQuality;
            if (sizeFile / 1000000.0 > 0.2 && sizeFile / 1000000.0 <= 0.5) {
                sizeQuality = 85
            } else if (sizeFile / 1000000.0 > 0.5 && sizeFile / 1000000.0 <= 1) {
                sizeQuality = 80
            }
            if (sizeFile / 1000000.0 > 1) {
                sizeQuality = 70
            }



            let engine = {
                jpg: {
                    engine: 'mozjpeg',
                    command: ['-quality', sizeQuality]
                },
            };
            let array = engine.jpg.command.concat('-outfile', newListFiles[i], nameFileInBuffer, );
            wasSize += statSync(nameFileInBuffer).size
            execFileSync(mozjpeg, array);



            nowSize += statSync(newListFiles[i]).size
            bar1.increment();
            fs.appendFileSync(siteName, newListFiles[i] + '\n', 'utf8');
            fs.utimesSync(newListFiles[i], statSync(nameFileInBuffer).atime, timeModif)
            fs.unlinkSync(nameFileInBuffer, function (err) {
                if (err) {
                    console.log('Ошибка при удалении файла ');
                    throw err
                }
            });
        } catch (err) {
            fs.appendFileSync(join(logdir, 'erorrs.txt'),
                '\n' + newListFiles[i] + '\n',
                'utf8');
            fs.renameSync(nameFileInBuffer, newListFiles[i], function (err) {
                if (err) {
                    console.log('Ошибка при переносе файла ');
                    throw err
                }
            });
            //            throw err
        }
    }
    fs.appendFileSync(join(logdir, 'compress-dir.txt'),
        '\n' + resume_dirs[i] + '\n',
        'utf8');

    if (fs.existsSync(join(logdir, 'compress-dir.txt'))) {
        fs.readFileSync(join(logdir, 'compress-dir.txt'), 'utf-8').split(/\r?\n/).forEach(line => {
            set_compress_dir.add(line);
        })
    }

    fs.appendFileSync(join(logdir, 'resultSize.csv'),
        resume_dirs[i] + ',' + wasSize / 1000000.0 + ',' + nowSize / 1000000.0 + '\n',
        'utf8');

    bar1.stop();

    let waitTill = new Date(new Date().getTime() + 10 * 1000);
    while (waitTill > new Date()) {}

}