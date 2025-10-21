# Multi-User Board Collaboration Test Guide

## Overview
This guide tests the enhanced multi-user board collaboration features in the Trello-like app.

## Prerequisites
1. Start the development environment:
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

2. Ensure all services are running:
   - Backend: http://localhost:8000
   - Frontend: http://localhost:3000
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

## Test Scenarios

### 1. WebSocket Connection Test
**Objective**: Verify WebSocket connections work without 403 errors

**Steps**:
1. Open browser to http://localhost:3000
2. Login with a user account
3. Create a new board
4. Open browser developer tools (F12)
5. Check console for WebSocket connection logs
6. Verify "Connected" status appears in the UI

**Expected Results**:
- WebSocket connects successfully
- No 403 Forbidden errors in console
- Connection status shows "Connected"
- Board state is received via WebSocket

### 2. User Invitation Flow
**Objective**: Test the complete invite flow from owner to invited user

**Steps**:
1. **As Board Owner**:
   - Open a board
   - Click "Invite" button
   - Enter email of another user
   - Select role (Member/Admin)
   - Click "Send Invite"
   - Verify modal closes automatically on success

2. **As Invited User**:
   - Login with the invited user account
   - Check notification bell for new invitation
   - Click on the notification
   - Verify board appears in available boards
   - Open the board and verify access

**Expected Results**:
- Invite modal closes automatically on success
- Invited user receives notification
- Board appears in invited user's board list
- Invited user can access the board
- WebSocket connection works for invited user

### 3. Real-time Collaboration
**Objective**: Test real-time updates between multiple users

**Steps**:
1. **Setup**:
   - Open board in two different browser windows/tabs
   - Login as different users in each window
   - Both users should be connected to the same board

2. **Test Real-time Updates**:
   - User 1: Create a new list
   - User 2: Should see the new list appear automatically
   - User 1: Create a new card
   - User 2: Should see the new card appear automatically
   - User 1: Move a card to different list
   - User 2: Should see the card move automatically
   - User 1: Update card details
   - User 2: Should see the updates automatically

**Expected Results**:
- All changes appear in real-time for both users
- No page refresh required
- Connection status shows "Connected" for both users
- Console shows WebSocket messages being received

### 4. Notification System
**Objective**: Test the notification bell and real-time notifications

**Steps**:
1. **Setup**:
   - User A: Create a board and invite User B
   - User B: Login and check notifications

2. **Test Notifications**:
   - User A: Invite User B to board
   - User B: Should see notification bell with red badge
   - User B: Click notification bell
   - User B: Should see invitation notification
   - User B: Click on notification
   - User B: Should be taken to the board

**Expected Results**:
- Notification bell shows unread count
- Notifications appear in real-time
- Clicking notification navigates to board
- Notifications can be marked as read

### 5. Connection Status Indicators
**Objective**: Test connection status and reconnection

**Steps**:
1. **Normal Connection**:
   - Open board
   - Verify "Connected" status is shown
   - Check browser console for connection logs

2. **Connection Issues**:
   - Disconnect internet briefly
   - Verify "Disconnected" status appears
   - Reconnect internet
   - Verify automatic reconnection and "Connected" status

**Expected Results**:
- Connection status accurately reflects WebSocket state
- Automatic reconnection on network issues
- Clear visual indicators of connection state

## Troubleshooting

### Common Issues

1. **WebSocket 403 Errors**:
   - Check that backend is running on single worker (not Gunicorn with multiple workers)
   - Verify WebSocket URL is correct: `ws://localhost:8000/api/v1/ws/board/{boardId}?token={token}`
   - Check browser console for detailed error messages

2. **Invitation Not Working**:
   - Verify user email exists in database
   - Check that user is not already a member
   - Verify notification system is working

3. **Real-time Updates Not Working**:
   - Check WebSocket connection status
   - Verify Redis is running and accessible
   - Check browser console for WebSocket messages

4. **Notifications Not Appearing**:
   - Verify global WebSocket connection for notifications
   - Check notification bell is included in layout
   - Verify notification API endpoints are working

### Debug Commands

1. **Check Backend Logs**:
   ```bash
   docker-compose -f docker-compose.dev.yml logs backend
   ```

2. **Check Redis Connection**:
   ```bash
   docker-compose -f docker-compose.dev.yml exec redis redis-cli ping
   ```

3. **Check Database**:
   ```bash
   docker-compose -f docker-compose.dev.yml exec postgres psql -U tasker -d tasker_db -c "SELECT * FROM board_members;"
   ```

## Success Criteria

✅ **WebSocket 403 Issues Fixed**:
- No 403 Forbidden errors on WebSocket connections
- Single worker configuration prevents connection issues
- Proper URL routing with API prefix

✅ **Invite Flow Working**:
- Modal closes automatically on successful invite
- Users cannot invite themselves
- Board members table is updated correctly
- Invited users receive notifications

✅ **Notification System**:
- Bell UI shows unread count
- Real-time notification delivery
- Clicking notifications navigates to boards
- Notifications can be marked as read

✅ **Frontend Connection Status**:
- Accurate connection status indicators
- Proper WebSocket error handling
- Automatic reconnection on network issues
- Clear visual feedback

✅ **Real-time Collaboration**:
- Changes appear instantly for all connected users
- No page refresh required
- WebSocket messages are properly handled
- Board state synchronization works

## Additional Features Implemented

- **Enhanced Error Handling**: Better WebSocket error messages and logging
- **Connection Status**: Real-time connection status indicators
- **Automatic Reconnection**: Smart reconnection logic that avoids infinite loops
- **Notification System**: Complete bell UI with real-time updates
- **Invite Flow**: Seamless user invitation with automatic modal closure
- **Board Access Control**: Proper permission checking for WebSocket connections
- **Real-time Updates**: Comprehensive real-time collaboration features

The multi-user board collaboration system is now fully functional with proper error handling, real-time updates, and a complete notification system.
