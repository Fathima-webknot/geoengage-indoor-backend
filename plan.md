# 🎯 GeoEngage Indoor POC - Complete Implementation Plan

**Date:** February 26, 2026  
**Version:** 1.0

---

## 📊 **1. DATABASE SCHEMA**

### **1.1 users**
```sql
CREATE TABLE users (
   id SERIAL PRIMARY KEY,
   firebase_uid VARCHAR(128) UNIQUE NOT NULL,
   email VARCHAR(255) NOT NULL,
   name VARCHAR(255),
   role VARCHAR(20) NOT NULL DEFAULT 'user',
   fcm_token TEXT,
   created_at TIMESTAMP NOT NULL DEFAULT NOW(),
   CONSTRAINT role_check CHECK (role IN ('user', 'admin'))
);

CREATE INDEX idx_users_firebase_uid ON users(firebase_uid);
```

**Notes:**
- `firebase_uid` uniquely links Firebase user (from Google Sign-In)
- `fcm_token` nullable (if user denies notification permission)
- Role defaults to 'user'

---

### **1.2 floors**
```sql
CREATE TABLE floors (
   id SERIAL PRIMARY KEY,
   name VARCHAR(100) NOT NULL,
   floor_number INT NOT NULL,
   created_at TIMESTAMP NOT NULL DEFAULT NOW(),
   CONSTRAINT unique_floor_number UNIQUE (floor_number)
);
```

**Notes:**
- Single venue assumed for POC
- `floor_number` unique (e.g., 0 = Ground, 1 = First Floor)

---

### **1.3 zones**
```sql
CREATE TABLE zones (
   id SERIAL PRIMARY KEY,
   floor_id INT NOT NULL REFERENCES floors(id) ON DELETE CASCADE,
   name VARCHAR(100) NOT NULL,
   polygon_coordinates JSONB NOT NULL,
   created_at TIMESTAMP NOT NULL DEFAULT NOW(),
   CONSTRAINT unique_zone_per_floor UNIQUE (floor_id, name)
);

CREATE INDEX idx_zones_floor_id ON zones(floor_id);
CREATE INDEX idx_zones_name ON zones(name);
```

**Notes:**
- `name` must match exactly with IndoorAtlas geofence name (case-sensitive)
- `polygon_coordinates` format: `[[lng, lat], [lng, lat], ...]`
- Zone name unique per floor for matching with SDK

---

### **1.4 campaigns**
```sql
CREATE TABLE campaigns (
   id SERIAL PRIMARY KEY,
   zone_id INT NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
   message TEXT NOT NULL,
   active BOOLEAN NOT NULL DEFAULT FALSE,
   created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_campaigns_zone_id ON campaigns(zone_id);
CREATE INDEX idx_campaigns_active ON campaigns(active);
```

**Notes:**
- Only one active campaign per zone (enforced by backend logic)
- `message` is the notification text sent via FCM

---

### **1.5 events**
```sql
CREATE TABLE events (
   id SERIAL PRIMARY KEY,
   user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
   zone_id INT NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
   entered_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_events_zone_id ON events(zone_id);
CREATE INDEX idx_events_entered_at ON events(entered_at);
```

**Notes:**
- Logs every zone entry for analytics
- No exit event (only entry tracked)

---

### **1.6 notifications**
```sql
CREATE TABLE notifications (
   id SERIAL PRIMARY KEY,
   user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
   campaign_id INT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
   status VARCHAR(20) NOT NULL,
   fcm_message_id TEXT,
   created_at TIMESTAMP NOT NULL DEFAULT NOW(),
   clicked_at TIMESTAMP NULL,
   CONSTRAINT status_check CHECK (status IN ('sent', 'failed'))
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_campaign_id ON notifications(campaign_id);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_notifications_clicked_at ON notifications(clicked_at);
```

**Notes:**
- `clicked_at` NULL until user taps notification
- Used for CTR calculation: `COUNT(clicked_at IS NOT NULL) / COUNT(*)`

---

### **1.7 CTR Calculation Query Example**
```sql
-- CTR for specific campaign
SELECT
   COUNT(*) FILTER (WHERE clicked_at IS NOT NULL)::float / NULLIF(COUNT(*), 0) AS ctr
FROM notifications
WHERE campaign_id = 5;

-- CTR for specific zone (all campaigns)
SELECT
   z.name AS zone_name,
   COUNT(n.*) AS total_sent,
   COUNT(n.clicked_at) AS total_clicks,
   (COUNT(n.clicked_at)::float / NULLIF(COUNT(n.*), 0)) AS ctr
FROM zones z
JOIN campaigns c ON c.zone_id = z.id
JOIN notifications n ON n.campaign_id = c.id
WHERE z.id = 3
GROUP BY z.id, z.name;
```

---

## 🔌 **2. API ENDPOINTS**

### **Authentication**
All endpoints (except auth) require Firebase ID token in header:
```
Authorization: Bearer <Firebase_ID_Token>
```

---

### **2.1 POST `/register-device`**

**Purpose:** Register or update user's FCM token for push notifications

**When Called:** After Google Sign-In + FCM token obtained

**Request Headers:**
```json
{
  "Authorization": "Bearer <Firebase_ID_Token>",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "fcm_token": "fL8sK3dP9mQ:APA91bH7vX..."
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Device registered successfully"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Invalid token"
}
```

**Backend Logic:**
1. Verify Firebase ID token
2. Extract `uid`, `email`, `name` from token
3. `INSERT ... ON CONFLICT (firebase_uid) DO UPDATE` user record
4. Update `fcm_token` field
5. Return success

---

### **2.2 GET `/me`**

**Purpose:** Get current user profile

**When Called:** After login to sync user data

**Request Headers:**
```json
{
  "Authorization": "Bearer <Firebase_ID_Token>"
}
```

**Request Body:** None

**Response (Success):**
```json
{
  "id": 1,
  "email": "user@gmail.com",
  "name": "Anurag Shetty",
  "role": "user",
  "firebase_uid": "Xk9pL2mN3oQ..."
}
```

**Response (Error):**
```json
{
  "error": "Unauthorized"
}
```

---

### **2.3 GET `/zones`**

**Purpose:** Get all zones with polygon coordinates for geofencing

**When Called:** On MapScreen mount

**Request Headers:**
```json
{
  "Authorization": "Bearer <Firebase_ID_Token>"
}
```

**Query Parameters:**
- `floor_id` (optional): Filter by floor (e.g., `?floor_id=1`)

**Request Body:** None

**Response (Success):**
```json
[
  {
    "id": 1,
    "floor_id": 1,
    "name": "Pantry",
    "polygon_coordinates": [
      [77.5946, 12.9716],
      [77.5948, 12.9716],
      [77.5948, 12.9714],
      [77.5946, 12.9714],
      [77.5946, 12.9716]
    ]
  },
  {
    "id": 2,
    "floor_id": 1,
    "name": "Electronics Store",
    "polygon_coordinates": [
      [77.5950, 12.9716],
      [77.5952, 12.9716],
      [77.5952, 12.9714],
      [77.5950, 12.9714],
      [77.5950, 12.9716]
    ]
  }
]
```

**Response (Error):**
```json
{
  "error": "No zones found"
}
```

**Notes:**
- `polygon_coordinates` format: `[[longitude, latitude], ...]`
- Coordinates should form a closed polygon (first point = last point)

---

### **2.4 POST `/event`**

**Purpose:** Log zone entry event and trigger notification if campaign is active

**When Called:** When IndoorAtlas SDK triggers `didEnterRegion` callback

**Request Headers:**
```json
{
  "Authorization": "Bearer <Firebase_ID_Token>",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "zone_name": "Pantry",
  "floor_id": 1
}
```

**Response (Success - Notification Sent):**
```json
{
  "success": true,
  "notification_sent": true,
  "campaign_message": "Welcome to Pantry - 20% off all snacks today!"
}
```

**Response (Success - No Campaign):**
```json
{
  "success": true,
  "notification_sent": false,
  "message": "Event logged, no active campaign"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Zone not found"
}
```

**Backend Logic:**
1. Verify Firebase token → get user
2. Find zone by `name` + `floor_id`: `SELECT id FROM zones WHERE name = ? AND floor_id = ?`
3. Insert event: `INSERT INTO events (user_id, zone_id, entered_at) VALUES (?, ?, NOW())`
4. Check active campaign: `SELECT * FROM campaigns WHERE zone_id = ? AND active = true`
5. If campaign exists:
   - Get user's `fcm_token`
   - Send FCM notification
   - Insert notification record: `INSERT INTO notifications (user_id, campaign_id, status, fcm_message_id) VALUES (...)`
6. Return response

---

### **2.5 GET `/notifications`**

**Purpose:** Get notification history for logged-in user

**When Called:** When user opens NotificationHistoryScreen

**Request Headers:**
```json
{
  "Authorization": "Bearer <Firebase_ID_Token>"
}
```

**Query Parameters:**
- `limit` (optional, default: 50): Max results
- `offset` (optional, default: 0): Pagination offset

**Request Body:** None

**Response (Success):**
```json
[
  {
    "id": 10,
    "campaign_id": 5,
    "message": "Welcome to Pantry - 20% off all snacks today!",
    "zone_name": "Pantry",
    "created_at": "2026-02-26T10:30:00Z",
    "clicked": false
  },
  {
    "id": 9,
    "campaign_id": 3,
    "message": "Check out new arrivals at Electronics Store",
    "zone_name": "Electronics Store",
    "created_at": "2026-02-25T14:15:00Z",
    "clicked": true
  }
]
```

**Response (Empty):**
```json
[]
```

**Notes:**
- Sorted by `created_at` DESC (newest first)
- `clicked` field derived from `clicked_at IS NOT NULL`
- Don't expose `clicked_at` timestamp to user (only boolean for UI)

---

### **2.6 POST `/notification-click`**

**Purpose:** Track when user taps on a notification (for CTR analytics)

**When Called:** When user taps push notification and app opens

**Request Headers:**
```json
{
  "Authorization": "Bearer <Firebase_ID_Token>",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "campaign_id": 5
}
```

**Response (Success):**
```json
{
  "success": true
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Notification not found"
}
```

**Backend Logic:**
1. Verify Firebase token → get user
2. Find notification: `SELECT * FROM notifications WHERE user_id = ? AND campaign_id = ? ORDER BY created_at DESC LIMIT 1`
3. Update `clicked_at`: `UPDATE notifications SET clicked_at = NOW() WHERE id = ?`
4. Return success

---

### **2.7 GET `/floors`** (Optional - for future multi-floor support)

**Purpose:** Get all floors in venue

**When Called:** On app initialization (for floor picker UI)

**Request Headers:**
```json
{
  "Authorization": "Bearer <Firebase_ID_Token>"
}
```

**Request Body:** None

**Response (Success):**
```json
[
  {
    "id": 1,
    "name": "Ground Floor",
    "floor_number": 0
  },
  {
    "id": 2,
    "name": "First Floor",
    "floor_number": 1
  }
]
```

---

## 📲 **3. FCM PUSH NOTIFICATION PAYLOAD**

**Sent by Backend to User's Device via FCM:**

```json
{
  "notification": {
    "title": "Special Offer!",
    "body": "Welcome to Pantry - 20% off all snacks today!",
    "sound": "default"
  },
  "data": {
    "type": "campaign_notification",
    "campaign_id": "5",
    "zone_id": "1",
    "zone_name": "Pantry"
  },
  "android": {
    "priority": "high",
    "notification": {
      "channel_id": "geoengage_offers",
      "click_action": "FLUTTER_NOTIFICATION_CLICK",
      "color": "#FF5722"
    }
  },
  "apns": {
    "payload": {
      "aps": {
        "alert": {
          "title": "Special Offer!",
          "body": "Welcome to Pantry - 20% off all snacks today!"
        },
        "badge": 1,
        "sound": "default"
      }
    }
  }
}
```

**Mobile Handling:**
```javascript
// When notification received (app in foreground)
messaging().onMessage(remoteMessage => {
  // Show in-app alert
});

// When user taps notification
messaging().onNotificationOpenedApp(remoteMessage => {
  const campaignId = remoteMessage.data.campaign_id;
  // Track click
  API.post('/notification-click', { campaign_id: campaignId });
  // Navigate to history screen
});
```

---

## 📱 **4. MOBILE APP SCREENS**

### **4.1 AuthScreen** (`screens/AuthScreen.js`)

**Purpose:** User authentication

**Components:**
- App logo/branding
- "Continue with Google" button (styled with Google branding)
- Company tagline/description below button

**Flow:**
1. User taps "Continue with Google"
2. Firebase Google Sign-In popup
3. On success:
   - Get Firebase ID token
   - Request notification permission
   - Get FCM token (if granted)
   - Call `POST /register-device`
   - Navigate to MapScreen

**UI Elements:**
- Logo at top center
- Tagline text
- Google Sign-In button (Material Design)
- Terms & Privacy links (optional)

---

### **4.2 MapScreen** (`screens/MapScreen.js`)

**Purpose:** Main screen showing floor plan with user's position

**Components:**
- Custom floor plan image (from assets or IndoorAtlas)
- Blue dot showing user's position
- Zone boundaries (optional visual overlay)
- Current floor indicator (e.g., "Ground Floor")
- Notification bell icon (top right) → opens NotificationHistoryScreen

**IndoorAtlas Integration:**
- Listen to `onLocationChanged` events
- Update blue dot position using coordinate conversion
- Monitor geofence entry/exit events

**Flow:**
1. Initialize IndoorAtlas SDK
2. Fetch zones from `GET /zones`
3. Register geofences with IndoorAtlas
4. Start positioning
5. Update blue dot in real-time
6. On zone entry → send `POST /event`
7. Show notification if received (foreground)

**UI Elements:**
- Floor plan ImageBackground
- Animated blue dot (View with pulse animation)
- Top bar: Floor name, notification icon
- Bottom sheet (optional): Zone info when inside

---

### **4.3 NotificationHistoryScreen** (`screens/NotificationHistoryScreen.js`)

**Purpose:** Display past notifications

**Components:**
- List of notification cards
- Pull-to-refresh functionality
- Empty state (no notifications)

**Data Source:**
- Fetch from `GET /notifications` on mount
- Refresh on pull-down

**Flow:**
1. Fetch notifications
2. Display in reverse chronological order
3. User can pull to refresh
4. Each card shows:
   - Notification message
   - Zone name
   - Time ago (e.g., "2 hours ago")

**UI Elements:**
- FlatList with NotificationCard components
- RefreshControl for pull-to-refresh
- Empty state with icon + message

---

### **4.4 ProfileScreen** (`screens/ProfileScreen.js`) - Optional

**Purpose:** User profile and settings

**Components:**
- User info (name, email from `GET /me`)
- Logout button
- App version info

**Flow:**
1. Display user data
2. Logout → Clear Firebase session → Navigate to AuthScreen

**UI Elements:**
- Avatar placeholder
- Name and email text
- Logout button (red)
- App version at bottom

---

## 🛠️ **5. KEY SERVICES & UTILITIES**

### **5.1 AuthService** (`services/AuthService.js`)
- Google Sign-In with Firebase
- Token management
- Auto-register with backend

### **5.2 FCMService** (`services/FCMService.js`)
- Request notification permissions
- Get FCM token
- Handle foreground notifications
- Handle notification clicks

### **5.3 APIService** (`services/APIService.js`)
- Axios instance with Firebase token interceptor
- All backend API calls
- Error handling

### **5.4 IndoorAtlasService** (`services/IndoorAtlasService.js`)
- Initialize SDK
- Start/stop positioning
- Get floor plan data
- Coordinate conversion

### **5.5 GeofenceManager** (`services/GeofenceManager.js`)
- Fetch zones from backend
- Create IAPolygonGeofence objects
- Register geofences with IndoorAtlas
- Handle entry/exit callbacks
- Cooldown management (1 hour default)

### **5.6 CooldownManager** (`utils/cooldown.js`)
- Store last notified time per zone
- Check if cooldown period elapsed
- Configurable cooldown duration (1 hour → 24 hours)

---

## 🎨 **6. UI COMPONENTS**

### **6.1 NotificationCard** (`components/NotificationCard.js`)
- Material Design card
- Notification message text
- Zone name + timestamp
- No "clicked" indicator (hidden from user)

### **6.2 BlueDot** (`components/BlueDot.js`)
- Animated View (pulse effect)
- Positioned absolutely on floor plan
- Blue circle with white border

### **6.3 GoogleSignInButton** (`components/GoogleSignInButton.js`)
- Styled with official Google branding
- Google logo + "Continue with Google" text
- Material Design shadow/elevation

---

## 📦 **7. TECH STACK**

| Component | Technology |
|-----------|-----------|
| Framework | React Native |
| Navigation | React Navigation |
| UI Library | React Native Paper (Material Design) |
| Maps/Positioning | IndoorAtlas SDK |
| Auth | Firebase Auth (Google Sign-In only) |
| Push Notifications | Firebase Cloud Messaging (FCM) |
| HTTP Client | Axios |
| State Management | React Context API |
| Local Storage | AsyncStorage |
| Date Formatting | date-fns or Moment.js |

---

## 🔄 **8. KEY WORKFLOWS**

### **8.1 Initial Setup Flow**
```
User opens app
  ↓
AuthScreen → "Continue with Google"
  ↓
Firebase Google Sign-In
  ↓
Get Firebase ID Token
  ↓
Request Notification Permission
  ↓
Get FCM Token (if granted)
  ↓
POST /register-device { fcm_token }
  ↓
Navigate to MapScreen
  ↓
Fetch zones (GET /zones)
  ↓
Register geofences with IndoorAtlas
  ↓
Start positioning
```

### **8.2 Zone Entry Flow**
```
User enters zone (physical movement)
  ↓
IndoorAtlas SDK: didEnterRegion(region)
  ↓
Check cooldown (last notified < 1 hour ago?)
  ↓
If cooldown active → SKIP
  ↓
If cooldown expired:
  ↓
POST /event { zone_name, floor_id }
  ↓
Backend checks active campaign
  ↓
If campaign active:
  ↓
Backend sends FCM notification
  ↓
User's phone receives notification
  ↓
If app in foreground → show alert
  ↓
User taps notification
  ↓
POST /notification-click { campaign_id }
  ↓
Navigate to NotificationHistoryScreen
```

### **8.3 Notification Click Tracking Flow**
```
User taps notification
  ↓
App opens (from background/killed state)
  ↓
Extract campaign_id from notification data
  ↓
POST /notification-click { campaign_id }
  ↓
Backend updates clicked_at timestamp
  ↓
Navigate to NotificationHistoryScreen
```

---

## ⏱️ **9. COOLDOWN MECHANISM**

**Purpose:** Prevent spamming user with notifications

**Logic:**
```javascript
// Store in AsyncStorage
{
  "zone_1": "2026-02-26T10:30:00Z",
  "zone_2": "2026-02-26T11:15:00Z"
}

// Check before sending event
const lastNotified = await AsyncStorage.getItem(`zone_${zoneId}_last_notified`);
const cooldownMs = 60 * 60 * 1000; // 1 hour (configurable)

if (lastNotified && (Date.now() - new Date(lastNotified) < cooldownMs)) {
  // Still in cooldown period → SKIP
  return;
}

// Cooldown expired → send event
await API.post('/event', { zone_name, floor_id });

// Update last notified time
await AsyncStorage.setItem(`zone_${zoneId}_last_notified`, new Date().toISOString());
```

**Configuration:**
- Default: 1 hour
- Easily changeable to 24 hours: `const cooldownMs = 24 * 60 * 60 * 1000;`

---

## 📊 **10. ADMIN DASHBOARD ENDPOINTS** (Not in Mobile App)

**Note:** These are web dashboard only, not implemented in mobile app

- `POST /campaigns` - Create campaign
- `PUT /campaigns/{id}` - Activate/deactivate campaign
- `GET /campaigns` - List all campaigns
- `GET /analytics` - Get zone entries, CTR, clicks data

**Admin Analytics Data:**
```json
{
  "zone_entries": [
    { "zone_name": "Pantry", "count": 42 },
    { "zone_name": "Electronics Store", "count": 35 }
  ],
  "notifications_sent": 30,
  "clicks": 12,
  "ctr": 0.4,
  "top_zones": [
    { "zone_name": "Pantry", "ctr": 0.45 },
    { "zone_name": "Electronics Store", "ctr": 0.35 }
  ]
}
```

---

## ✅ **11. SUMMARY CHECKLIST**

### **Backend Team:**
- [ ] Set up PostgreSQL database with schema above
- [ ] Implement Firebase Admin SDK for token verification
- [ ] Implement all 6 user endpoints
- [ ] Implement FCM integration for sending notifications
- [ ] Ensure zone name matching (case-sensitive)
- [ ] Add indexes for performance
- [ ] Test notification sending flow

### **Frontend Team:**
- [ ] Initialize React Native project
- [ ] Set up Firebase (Google Sign-In + FCM)
- [ ] Integrate IndoorAtlas SDK
- [ ] Build 3 core screens (Auth, Map, History)
- [ ] Implement geofence registration
- [ ] Implement zone entry detection
- [ ] Implement notification handling
- [ ] Implement cooldown mechanism
- [ ] Test on physical device at venue

---

## 🚀 **12. DEPLOYMENT NOTES**

### **Environment Variables:**
```env
# Backend
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=your-service-account@...
FIREBASE_PRIVATE_KEY=...
FCM_SERVER_KEY=...
DATABASE_URL=postgresql://...

# Mobile App
FIREBASE_API_KEY=AIza...
FIREBASE_AUTH_DOMAIN=...
FIREBASE_PROJECT_ID=...
INDOORATLAS_API_KEY=...
API_BASE_URL=https://api.geoengage.com
```

### **Testing Checklist:**
- [ ] Google Sign-In works
- [ ] FCM token registration successful
- [ ] Zones fetched correctly
- [ ] Geofences registered with IndoorAtlas
- [ ] Blue dot positioning accurate
- [ ] Zone entry event triggered
- [ ] Notification received
- [ ] Notification click tracked
- [ ] History screen shows notifications
- [ ] Cooldown prevents spam
- [ ] CTR calculation correct in admin dashboard

---

**END OF PLAN**
