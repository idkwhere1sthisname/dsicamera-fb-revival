# Facebook Integration for DSi Camera Revival
Facebook integration for Nintendo DSi Camera Revival (kinda)

## Why?

This is such a niche feature, that no one bothered to revive, so I decided to do that.

<div align="center">
<img src="https://img.idkwh.ct8.pl/fb_twl/img1.jpg" width="309" height="309"/><img src="https://img.idkwh.ct8.pl/fb_twl/img2.jpg" width="309"/><br/><img src="https://img.idkwh.ct8.pl/fb_twl/img3.jpg" width="309"/><img src="https://img.idkwh.ct8.pl/fb_twl/log1.png" height="242"/>
</div>

Since Facebook doesn't allow access to uploading photos from an application through its API, this server uploads the photos to the local directory, in `/uploads/`.

## ARM9 Patching

1. Extract the Nintendo DSi Camera ARM9 file using [TinkeDSi](https://github.com/R-YaTian/TinkeDSi).
2. Open it in a Hex editor.
3. Search for `fb.t.app.nintendowifi.net`.
4. Replace the URLs to your IP/Domain (you might need to null out extra bytes, if the URL is shorter, if so, rewrite the full path).
5. Replace the ARM9 in the stock DSi Camera .NDS with your custom one and rebuild the ROM.
6. Run the server to create a configuration and a key file.

You can run the server with HTTPS, but it was not tested, so you might need to replace the certificate chain in `/static/` with your own.

**In the login dialog, please don't input any real information, as it doesn't actually communicate with Facebook or post your pictures on there.**

The app might say that the save data is corrupt, but that's fine, (it doesn't actually delete your photos), it just makes you go through the tutorial again, though
