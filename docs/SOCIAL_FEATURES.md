# Social Features & Community Documentation

## Overview

The Federal Bills Explainer includes comprehensive social and community features that enable user interaction, collaboration, and engagement with federal legislation. This system provides authentication, bookmarking, collections, commenting, voting, notifications, and social sharing capabilities.

## Table of Contents

1. [User Authentication](#user-authentication)
2. [Bookmarks & Favorites](#bookmarks--favorites)
3. [Bill Collections](#bill-collections)
4. [Comments System](#comments-system)
5. [Voting System](#voting-system)
6. [Notifications](#notifications)
7. [Bill Watching](#bill-watching)
8. [Social Sharing](#social-sharing)
9. [API Reference](#api-reference)
10. [Frontend Components](#frontend-components)
11. [Security Considerations](#security-considerations)

---

## User Authentication

### Features

- **User Registration**: Email-based registration with password validation
- **Login**: JWT-based authentication with access and refresh tokens
- **Email Verification**: Token-based email verification
- **Password Reset**: Secure password reset flow with time-limited tokens
- **Profile Management**: User profiles with avatar, bio, and reputation

### Authentication Flow

1. **Registration**:
   ```bash
   POST /auth/register
   {
     "email": "user@example.com",
     "username": "johndoe",
     "password": "SecurePass123",
     "full_name": "John Doe"
   }
   ```

2. **Login**:
   ```bash
   POST /auth/login
   {
     "email": "user@example.com",
     "password": "SecurePass123"
   }
   ```

3. **Token Response**:
   ```json
   {
     "access_token": "eyJhbGc...",
     "refresh_token": "eyJhbGc...",
     "token_type": "bearer"
   }
   ```

### Password Requirements

- Minimum 8 characters
- Maximum 128 characters
- Must contain uppercase, lowercase, and numbers
- Special characters recommended but not required

### Username Requirements

- 3-50 characters
- Alphanumeric and underscores only
- Must be unique across platform

---

## Bookmarks & Favorites

### Features

- Save bills for later reading
- Add personal notes to bookmarks
- Tag bookmarks for organization
- Quick access to saved bills

### API Endpoints

#### Create Bookmark
```bash
POST /social/bookmarks
{
  "bill_id": "118/hr/1234",
  "notes": "Important healthcare bill",
  "tags": ["healthcare", "priority"]
}
```

#### Get Bookmarks
```bash
GET /social/bookmarks?tags=healthcare&limit=50
```

#### Delete Bookmark
```bash
DELETE /social/bookmarks/118/hr/1234
```

### Frontend Component

```tsx
import { BookmarkButton } from '@/components';

<BookmarkButton
  billId="118/hr/1234"
  initialBookmarked={false}
/>
```

---

## Bill Collections

### Features

- Create custom collections of bills
- Organize bills by topic, urgency, or custom criteria
- Public and private collections
- Add notes to collection items
- Share public collections with community

### API Endpoints

#### Create Collection
```bash
POST /social/collections
{
  "name": "Climate Change Bills",
  "description": "Bills related to climate action",
  "is_public": true
}
```

#### Get Collections
```bash
GET /social/collections?include_public=true
```

#### Add Bill to Collection
```bash
POST /social/collections/{collection_id}/items
{
  "bill_id": "118/hr/1234",
  "notes": "Key climate bill"
}
```

#### Delete Collection
```bash
DELETE /social/collections/{collection_id}
```

### Use Cases

- **Research Projects**: Organize bills for academic research
- **Advocacy Groups**: Track relevant legislation
- **Personal Interest**: Curate bills on topics you care about
- **Public Education**: Share bill collections with community

---

## Comments System

### Features

- Comment on bills
- Threaded discussions (reply to comments)
- Upvote/downvote comments
- Sort by top, new, or controversial
- Soft deletion (content preserved for context)
- Moderation tools (flagging)

### API Endpoints

#### Create Comment
```bash
POST /social/comments
{
  "bill_id": "118/hr/1234",
  "content": "This bill addresses important issues...",
  "parent_id": null  # For threaded replies
}
```

#### Get Comments
```bash
GET /social/comments?bill_id=118/hr/1234&sort=top&limit=50
```

#### Vote on Comment
```bash
POST /social/comments/{comment_id}/vote?vote_type=upvote
```

#### Delete Comment
```bash
DELETE /social/comments/{comment_id}
```

### Sorting Algorithms

- **Top**: Sorted by (upvotes - downvotes), highest first
- **New**: Sorted by creation time, newest first
- **Controversial**: Sorted by min(upvotes, downvotes), highest first

### Frontend Component

```tsx
import { CommentSection } from '@/components';

<CommentSection billId="118/hr/1234" />
```

---

## Voting System

### Features

- Upvote or downvote comments
- Vote toggle (click again to remove vote)
- Vote switching (change from upvote to downvote)
- Reputation system integration

### Vote Mechanics

1. **First Vote**: Records vote, increments counter
2. **Same Vote**: Removes vote, decrements counter (toggle)
3. **Different Vote**: Removes old vote, adds new vote (switch)

### Vote Counts

- **Upvotes**: Positive community sentiment
- **Downvotes**: Negative community sentiment
- **Score**: upvotes - downvotes

### API Endpoint

```bash
POST /social/comments/{comment_id}/vote?vote_type=upvote
POST /social/comments/{comment_id}/vote?vote_type=downvote
```

### Response

```json
{
  "message": "Vote recorded",
  "upvotes": 42,
  "downvotes": 3
}
```

---

## Notifications

### Features

- In-app notifications
- Email notifications (planned)
- Notification types:
  - Comment replies
  - Bill updates
  - Watch alerts
  - System messages

### API Endpoints

#### Get Notifications
```bash
GET /social/notifications?unread_only=true&limit=50
```

#### Mark as Read
```bash
POST /social/notifications/{notification_id}/read
```

#### Mark All Read
```bash
POST /social/notifications/read-all
```

### Notification Types

- `comment_reply`: Someone replied to your comment
- `bill_update`: Watched bill status changed
- `collection_shared`: Someone shared a collection with you
- `mention`: Someone mentioned you in a comment
- `system`: System announcements

### Notification Structure

```json
{
  "id": "uuid",
  "type": "comment_reply",
  "title": "New reply to your comment",
  "message": "User replied: 'I agree with your points...'",
  "link": "/bills/118/hr/1234#comment-xyz",
  "is_read": false,
  "created_at": "2025-11-13T10:30:00Z"
}
```

---

## Bill Watching

### Features

- Watch bills for status updates
- Configure notification preferences:
  - Email notifications
  - In-app notifications
  - Webhook notifications
- Track bill progress
- Get alerts on status changes

### API Endpoints

#### Watch Bill
```bash
POST /social/watch/118/hr/1234?notify_email=true&notify_in_app=true&webhook_url=https://example.com/webhook
```

#### Unwatch Bill
```bash
DELETE /social/watch/118/hr/1234
```

#### Get Watched Bills
```bash
GET /social/watch
```

### Webhook Integration

When bill status changes, POST request sent to webhook URL:

```json
{
  "bill_id": "118/hr/1234",
  "event": "status_change",
  "old_status": "introduced",
  "new_status": "passed",
  "timestamp": "2025-11-13T10:30:00Z",
  "bill_title": "Climate Action Bill"
}
```

---

## Social Sharing

### Features

- Share bills on social media platforms:
  - Facebook
  - Twitter
  - LinkedIn
  - Reddit
- Email sharing
- Copy link to clipboard
- Pre-formatted share text

### API Endpoints

#### Get Share Links
```bash
GET /sharing/link/118/hr/1234
```

#### Response
```json
{
  "bill_id": "118/hr/1234",
  "links": {
    "facebook": "https://www.facebook.com/sharer/...",
    "twitter": "https://twitter.com/intent/tweet?...",
    "linkedin": "https://www.linkedin.com/sharing/...",
    "reddit": "https://www.reddit.com/submit?...",
    "email": "mailto:?subject=...",
    "copy": "https://federalbills.example.com/bills/118/hr/1234"
  }
}
```

#### Share via Email
```bash
POST /sharing/email
{
  "bill_id": "118/hr/1234",
  "recipient_emails": ["friend@example.com"],
  "message": "Check out this important bill!"
}
```

### Frontend Component

```tsx
import { ShareButton } from '@/components';

<ShareButton
  billId="118/hr/1234"
  billTitle="Climate Action Bill"
/>
```

---

## API Reference

### Authentication Endpoints

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login with credentials
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user profile
- `POST /auth/password-reset` - Request password reset
- `POST /auth/password-reset/confirm` - Confirm password reset
- `POST /auth/verify-email/{token}` - Verify email address

### Social Endpoints

- `POST /social/bookmarks` - Create bookmark
- `GET /social/bookmarks` - Get user bookmarks
- `DELETE /social/bookmarks/{bill_id}` - Delete bookmark
- `POST /social/collections` - Create collection
- `GET /social/collections` - Get collections
- `POST /social/collections/{id}/items` - Add to collection
- `DELETE /social/collections/{id}` - Delete collection
- `POST /social/comments` - Create comment
- `GET /social/comments` - Get comments
- `POST /social/comments/{id}/vote` - Vote on comment
- `DELETE /social/comments/{id}` - Delete comment
- `GET /social/notifications` - Get notifications
- `POST /social/notifications/{id}/read` - Mark notification read
- `POST /social/notifications/read-all` - Mark all read
- `POST /social/watch/{bill_id}` - Watch bill
- `DELETE /social/watch/{bill_id}` - Unwatch bill
- `GET /social/watch` - Get watched bills

### Sharing Endpoints

- `POST /sharing/email` - Share via email
- `GET /sharing/link/{bill_id}` - Get share links

---

## Frontend Components

### LoginForm

User authentication form with email and password:

```tsx
import { LoginForm } from '@/components';

<LoginForm
  onSuccess={() => console.log('Logged in!')}
  onSwitchToRegister={() => setShowRegister(true)}
/>
```

### BookmarkButton

Toggle bookmark status for a bill:

```tsx
<BookmarkButton billId="118/hr/1234" />
```

### CommentSection

Complete commenting interface with voting:

```tsx
<CommentSection billId="118/hr/1234" />
```

### ShareButton

Social media sharing menu:

```tsx
<ShareButton
  billId="118/hr/1234"
  billTitle="Climate Action Bill"
/>
```

---

## Security Considerations

### Authentication

- **JWT Tokens**: Use secure, signed JWT tokens
- **Token Expiry**: Access tokens expire after 24 hours
- **Refresh Tokens**: Refresh tokens expire after 30 days
- **Password Hashing**: Bcrypt with salt
- **Email Verification**: Required for full account access

### Authorization

- **Ownership Checks**: Users can only modify their own content
- **Admin Privileges**: Special permissions for moderation
- **Rate Limiting**: Prevent abuse of endpoints
- **CSRF Protection**: Tokens for state-changing operations

### Data Privacy

- **Email Privacy**: Emails never publicly displayed
- **Profile Visibility**: Configurable privacy settings
- **Comment Deletion**: Soft deletion preserves context
- **User Data**: GDPR-compliant data handling

### Content Moderation

- **Flagging System**: Community-driven moderation
- **Admin Tools**: Review flagged content
- **Spam Prevention**: Rate limiting and detection
- **Abuse Reporting**: Quick reporting mechanism

---

## Best Practices

### For Users

1. **Strong Passwords**: Use unique, complex passwords
2. **Verify Email**: Complete email verification
3. **Respectful Comments**: Follow community guidelines
4. **Report Abuse**: Flag inappropriate content
5. **Privacy Settings**: Review and configure privacy

### For Developers

1. **Validate Input**: Sanitize all user input
2. **Rate Limiting**: Implement on all endpoints
3. **Error Handling**: Never expose sensitive data in errors
4. **Logging**: Log authentication attempts and changes
5. **Testing**: Comprehensive security testing

---

## Database Schema

### Users Table

- `id` (UUID): Primary key
- `email` (String): Unique email address
- `username` (String): Unique username
- `hashed_password` (String): Bcrypt hash
- `full_name` (String): Display name
- `bio` (Text): User biography
- `avatar_url` (String): Profile picture URL
- `reputation` (Integer): User reputation score
- `is_verified` (Boolean): Email verified
- `created_at` (DateTime): Registration date

### Bookmarks Table

- `id` (UUID): Primary key
- `user_id` (UUID): Foreign key to users
- `bill_id` (String): Bill identifier
- `notes` (Text): Personal notes
- `tags` (JSON): Array of tags
- `created_at` (DateTime): Bookmark date

### Collections Table

- `id` (UUID): Primary key
- `user_id` (UUID): Foreign key to users
- `name` (String): Collection name
- `description` (Text): Collection description
- `is_public` (Boolean): Public visibility
- `created_at` (DateTime): Creation date

### Comments Table

- `id` (UUID): Primary key
- `user_id` (UUID): Foreign key to users
- `bill_id` (String): Bill identifier
- `parent_id` (UUID): Parent comment (nullable)
- `content` (Text): Comment text
- `upvotes` (Integer): Upvote count
- `downvotes` (Integer): Downvote count
- `is_deleted` (Boolean): Soft deletion flag
- `created_at` (DateTime): Comment date

### Votes Table

- `id` (UUID): Primary key
- `user_id` (UUID): Foreign key to users
- `comment_id` (UUID): Foreign key to comments
- `vote_type` (String): 'upvote' or 'downvote'
- `created_at` (DateTime): Vote date

---

## Future Enhancements

### Planned Features

1. **User Reputation System**
   - Points for quality contributions
   - Badges and achievements
   - Leaderboard

2. **Advanced Moderation**
   - Automated spam detection
   - Community moderators
   - Appeal system

3. **Enhanced Notifications**
   - Push notifications
   - Digest emails
   - Custom notification rules

4. **Social Features**
   - User following
   - Activity feeds
   - Trending discussions

5. **Integration**
   - Third-party OAuth (Google, GitHub)
   - API webhooks for external services
   - Mobile app support

---

## Troubleshooting

### Common Issues

**Problem**: Cannot login

**Solutions**:
- Check email and password are correct
- Verify email has been confirmed
- Try password reset if forgotten
- Check account hasn't been disabled

**Problem**: Bookmarks not saving

**Solutions**:
- Ensure you're logged in
- Check network connection
- Verify bill ID is correct
- Clear browser cache

**Problem**: Comments not posting

**Solutions**:
- Ensure comment is not empty
- Check character limit (10,000)
- Verify you're not rate limited
- Refresh page and try again

---

## Support

For issues or questions:
- Check API documentation: `/docs`
- Review error messages in browser console
- Test endpoints with curl or Postman
- Open GitHub issue with details

---

## Contributing

When adding social features:

1. Update database models
2. Create API endpoints
3. Add frontend components
4. Write tests
5. Update this documentation
6. Submit pull request

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OAuth 2.0 Specification](https://oauth.net/2/)
- [GDPR Compliance](https://gdpr.eu/)
