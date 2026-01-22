# CBay - Online Auction Platform

A full-featured auction platform built with Django and Vue.js, allowing users to list items, place bids, ask questions, and follow sellers.

## 🎓 Team Members

**Group 52**

| Name | Assigned Tasks | Actual Contributions |
|------|---------------|---------------------|
| Acil | Assigned to implement Django Models for Questions and Answers, he was in charge of all cron jobs and notifications as well as frontend styling. Also responsible for deployment and all devops. | Completed all assigned tasks |
| Yasir | Assigned to implement user profile page and Pinia global store management | Implemented profile page with image upload functionality, built Pinia auth store with state management, and integrated authentication flow throughout the application |
| Rafi | Assigned to implement items listing, item details page, and search functionality | Built all item-related features including item creation with multi-image upload, item detail view, bidding interface, and advanced search with filtering and sorting |

## Deployment

**Application URL:** `https://group-52-cw-group-52-cw.apps.a.comp-teach.qmul.ac.uk/`

## Admin Credentials

- **Username:** `cbayboss`
- **Password:** `cbay123`


### 1. Sarah Chen
- **Username:** `sarahchen`
- **Password:** `AuctionBid2026!`

### 2. Marcus Rodriguez
- **Username:** `mrodriguez`
- **Password:** `SecureBid2026!`

### 3. Emily Watson
- **Username:** `emilywatson`
- **Password:** `Vintage2026Finds!`

### 4. James Okonkwo
- **Username:** `jamesokonkwo`
- **Password:** `BidMaster2026!`

### 5. Priya Sharma
- **Username:** `priyasharma`
- **Password:** `ArtAuction2026!`

## Advanced Features (Beyond Requirements)

This project goes significantly beyond the basic requirements with several advanced features:

### 1. **Social Following System**
- Users can follow sellers they're interested in
- Real-time follow/unfollow functionality via API
- Follower and following counts displayed on profiles
- Follow status shown on item detail pages

### 2. **Automated Email Notifications**
- **Auction Winners:** Automatic emails sent when auctions end with winning bid details
- **Sellers:** Notifications when items sell or auctions end without bids
- **Follower Updates:** Users receive emails when sellers they follow list new items
- Configured with Gmail SMTP for production use

### 3. **Cron Job Management Commands**
- `close_auctions`: Processes ended auctions, determines winners, sends emails
- `notify_followers`: Sends notifications to followers when new items are listed
- Both commands are production-ready for scheduled execution (hourly recommended)
- Comprehensive logging and error handling

### 4. **Full Internationalization (i18n)**
- Complete translation support built into the frontend
- **English and Spanish** translations provided
- All UI text, error messages, and confirmations are translatable
- Language switcher in footer for easy switching

### 5. **S3-Compatible Image Storage**
- Production deployment uses Amazon S3 for all image uploads
- Profile images and item images stored in cloud storage
- Automatic file organisation by upload type (`profile_images/`, `items/`)
- Local filesystem fallback for development
- Configured via `django-storages` and `boto3`

### 6. **Advanced Item Management**
- **Multi-image upload:** Up to 8 images per item with drag & drop
- **Image gallery:** Thumbnail navigation on item detail pages
- **"My Listings" filter:** Users can view only their own items
- **Delete functionality:** Item owners can delete their listings
- Ordered image display with user-controlled sequence
