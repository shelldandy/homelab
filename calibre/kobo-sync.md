# Actionable Items for Setting Up Kobo Sync with Calibre Web

Summarized from: https://jccpalmer.com/posts/setting-up-kobo-sync-with-calibre-web/

### **1. Configure Calibre Web for Kobo Sync**

- **Enable Kobo Sync**:

  - In Calibre Web’s **Admin settings** → **Edit Basic Configuration** → **Feature Configuration**, check:
    - _Enable Kobo sync_
    - _Proxy unknown requests to Kobo Store_
  - Ensure the _Server External Port_ matches Calibre Web’s port (default: `8083`).

- **User Settings**:
  - Under your user profile, enable _Sync only books in selected shelves with Kobo_.
  - Generate a **Kobo Sync Token URL** via _Create/View_ button and copy it.

---

### **2. Organize Shelves for Syncing**

- **Create/Edit Shelves**:
  - In Calibre Web, create shelves (e.g., “Fantasy,” “Sci-Fi”) or edit existing ones.
  - For each shelf, enable _Sync this shelf with Kobo device_.

---

### **3. Modify Kobo Configuration File**

- **Access Kobo’s Config File**:
  - Connect Kobo to a computer, navigate to the `.kobo/Kobo` folder.
  - Open `Kobo eReader.conf` (back up the file first).
  - Under `[OneStoreServices]`, replace the `api_endpoint=` line with the copied **Sync Token URL**.
  - Save changes and safely eject the Kobo.

---

### **4. Trigger Initial Sync**

- On the Kobo, manually sync via the **Sync icon** in the top toolbar.
- Allow time for Calibre Web to build its database and transfer books/metadata.

---

### **5. Troubleshooting & Tips**

- **External URL Issues**:

  - If using a reverse proxy/Cloudflare tunnel, use Calibre Web’s **local IP:port** (e.g., `http://192.168.x.x:8083`) instead of an external URL.
  - Ensure HTTP (not HTTPS) is used if encountering errors.

- **Missing Book Covers**:

  - Verify Calibre Web’s image URL settings (`image_host`, `image_url_template`) in the config.
  - Expose port `80` on the host if needed.

- **DRM Tip**:
  - For Kobo Store purchases, remove DRM before adding to Calibre to enable syncing.

---

### **6. Limitations**

- Syncing may not restore **Kobo Store/Overdrive covers** (generic covers may appear).
- Overdrive integration might require additional port mapping or configuration.

---

**Final Note**: This setup automates sideloading, but minor issues (e.g., covers) may persist. Regularly back up your Kobo config and Calibre library.
