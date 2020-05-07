(function() {
    function createDinoqodeCommand() {
        var services = {
                'amazonmusic': /.*music\.amazon\..*/,
                'applemusic': /.*\.apple\.com.*/,
                'spotify': /.*\.spotify\.com.*/,
                'aldilife': /.*\.lifestore-flat\.de.*/,
                'napster': /.*\.napster\.com.*/
            },
            type,
            service,
            url = location.href,
            cmd,
            title,
            artist,
            id,
            temp;

        type = window.prompt('Album (album = default) oder Song (song)?') || 'album';

        if (!service) {
            for(var serviceName in services) {
                if (services[serviceName].test(url)) {
                    service = serviceName;
                }
            }
        }

        if (service === 'applemusic') {
            id = document.querySelector('meta[name="apple:content_id"]').content;
            title = document.querySelector('h1.product-name').innerText;
            artist = document.querySelector('h2.product-creator a').innerText;
            arturl = document.querySelector('div.product-lockup__artwork-for-product img').srcset.split(' ')[5].replace('540w,','');

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

        } else if (service === 'aldilife' || service === 'napster') {
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

        copyToClipboard(cmd);
        window.alert('Copied!');
        return cmd;
    }

    function copyToClipboard(text) {
        if (window.clipboardData && window.clipboardData.setData) {
            /*IE specific code path to prevent textarea being shown while dialog is visible.*/
            return clipboardData.setData("Text", text);

        } else if (document.queryCommandSupported && document.queryCommandSupported("copy")) {
            var textarea = document.createElement("textarea");

            textarea.textContent = text;
            textarea.style.position = "fixed";  /* Prevent scrolling to bottom of page in MS Edge.*/
            document.body.appendChild(textarea);
            textarea.select();

            try {
                return document.execCommand("copy");  /* Security exception may be thrown by some browsers.*/
            } catch (ex) {
                console.warn("Copy to clipboard failed.", ex);
                return false;
            } finally {
                document.body.removeChild(textarea);
            }
        }
    }

    createDinoqodeCommand();
})();