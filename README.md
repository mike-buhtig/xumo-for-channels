# 📺 Xumo for Channels

**Xumo for Channels** is a containerized service that automatically generates a live M3U playlist and XMLTV EPG feed for **Xumo**, ready to serve to IPTV clients or middleware such as **NextPVR** and **Kodi**.

It includes a lightweight **Flask + Gevent** web server that starts instantly, serving a status page until the files are generated.  
Once ready, it provides direct download links for both the playlist and EPG feed.

The EPG and playlist generation logic is adapted from the open-source project  
👉 [BuddyChewChew/xumo-playlist-generator](https://github.com/BuddyChewChew/xumo-playlist-generator)

---

## 📜 Credits

- **Core EPG and Playlist Logic:** Adapted from [BuddyChewChew/xumo-playlist-generator](https://github.com/BuddyChewChew/xumo-playlist-generator)  
- **Enhancements, containerization, and web service:** Mike Farris (**mike-buhtig**)

---

## 🐳 Docker Quick Start

### 🧱 Build from Source
```bash
docker build -t xumo-for-channels .
📦 Pull Prebuilt Image
A prebuilt image is available on Docker Hub:
👉 https://hub.docker.com/r/mike1504/xumo-for-channels

bash
Copy code
docker pull mike1504/xumo-for-channels:latest
🚀 Run the Container
bash
Copy code
docker run -d \
  --name xumo-for-channels \
  -p 7781:7781 \
  -e XUMO_PORT=7781 \
  -e TZ=America/Chicago \
  --restart unless-stopped \
  mike1504/xumo-for-channels:latest
Then open your browser to:
👉 http://<server-ip>:7781/

The page will immediately display a status notice until the first playlist and EPG generation completes.

🧾 License & Attribution
This project is released under the MIT License.

Portions of this code are adapted from
BuddyChewChew/xumo-playlist-generator
and are used with attribution.

