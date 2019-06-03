/**
 * Liefert einen dinoqode Command-String für Musikservices zurück.
 * 
 * @param {String} type=album Album (album) oder Song (song)
 * @param {String} [service] Music Service (applemusic, amazonmusic)
 * @return {String}
 */
function createDinoqodeCommand(type, service) {
    type = type || 'album';

    var services = {
            'amazonmusic': /.*music\.amazon\..*/,
            'applemusic': /.*\.apple\.com.*/,
            'spotify': /.*\.spotify\.com.*/,
            'aldilife': /.*\.lifestore-flat\.de.*/
        },
        url = location.href,
        cmd,
        title,
        artist,
        id,
        temp;

    if (!service) {
        for(var serviceName in services) {
            if (services[serviceName].test(url)) {
                service = serviceName;
            }
        }
    }

    if (service === 'applemusic') {
        id = document.querySelector('meta[name="apple:content_id"]').content;
        title = document.querySelector('span.product-header__title').getAttribute('aria-label');
        artist = document.querySelector('span.product-header__identity a').innerText;
        arturl = document.querySelector('picture.we-artwork source:first-child').srcset.split(',')[2].replace(' 3x','');

    } else if (service === 'amazonmusic') {
        temp = url.split('/');

        if (temp && temp.length) {
            id = temp[temp.length - 1];
        }

        title = document.querySelector('.playlistHeaderDescription .viewTitle').innerText;
        artist = document.querySelector('.playlistHeaderDescription .artistLink a').innerText;
        arturl = document.querySelector('.albumArtWrapper img.renderImage').src

    } else if (service === 'spotify') {
        temp = url.split('/');

        if (temp && temp.length) {
            id = temp[temp.length - 1];
        }

        title = document.querySelector('.media-object .mo-info-name').title;
        artist = document.querySelector('.media-object .react-contextmenu-wrapper a').innerText;
        temp = document.querySelector('.media-object .cover-art-image').style.backgroundImage;

        if (temp) {
            arturl = temp.match(/url\("(.*)"\)/)[1];
        }

    } else if (service === 'aldilife') {
        id = document.querySelector('.blurred-image .image').style.backgroundImage.match(/url\(".*images\/Alb\.(.*)\/.*"\)/)[1];
        title = document.querySelector('.album-title').innerText;
        artist = document.querySelector('.artist-name').innerText;
        arturl = document.querySelector('.blurred-image .image').style.backgroundImage.match(/url\("(.*)"\)/)[1];
    }

    if (!id) {
        throw(new Error('Kein ID gefunden!'));
    }

    if (!title) {
        throw(new Error('Kein Title gefunden!'));
    }

    if (!artist) {
        throw(new Error('Kein Artist gefunden!'));
    }

    if (!arturl) {
        throw(new Error('Kein Cover gefunden!'));
    }

    // Title changes
    if (/Folge \d{1,3} - /.test(title)) {
        title = title.replace(/[Folge \d{1,3} ]-/, ':');
    }

    cmd = [
        service,
        type,
        id
    ].join(':');

    cmd = [
        cmd,
        title,
        artist,
        arturl
    ].join('|');

    copy(cmd);
    return cmd;
}