// Configuration
const API_BASE = window.location.origin;

// Set up Axios interceptor for JWT
axios.interceptors.request.use(config => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, error => Promise.reject(error));

// The global app state and controllers
const app = {
    state: {
        email: null,
        feedType: 'global',
        searchType: 'users',
        currentUser: null,
        activeChatUser: null
    },

    init() {
        if (localStorage.getItem('access_token')) {
            this.showMainView();
            this.fetchCurrentUser();
            this.navigate('feed');
        } else {
            this.showAuthView();
        }
    },

    // --- DOM Utilities ---
    showError(id, msg) {
        const el = document.getElementById(id);
        if (el) el.innerText = msg || '';
    },

    // --- Auth Logic ---
    showAuthView() {
        document.getElementById('main-view').classList.remove('active');
        document.getElementById('auth-view').classList.add('active');
        this.toggleAuthForm('login');
    },

    toggleAuthForm(type) {
        document.querySelectorAll('.auth-step').forEach(el => el.classList.remove('active'));
        if (type === 'login') {
            document.getElementById('form-login').classList.add('active');
            this.showError('login-error', '');
        } else if (type === 'signup') {
            document.getElementById('form-signup').classList.add('active');
            this.showError('signup-error', '');
        } else if (type === 'signup-otp') {
            document.getElementById('form-signup-otp').classList.add('active');
            this.showError('signup-otp-error', '');
        } else if (type === 'forgot-password') {
            document.getElementById('form-forgot-password').classList.add('active');
            this.showError('forgot-error', '');
        } else if (type === 'reset-password') {
            document.getElementById('form-reset-password').classList.add('active');
            this.showError('reset-error', '');
        }
    },

    async handleGoogleCredentialResponse(response) {
        try {
            document.body.classList.add('loading');
            const res = await axios.post(`${API_BASE}/auth/google`, {
                credential: response.credential
            });

            localStorage.setItem('access_token', res.data.access_token);
            this.showError('login-error', '');
            this.showMainView();
            this.fetchCurrentUser();
            this.navigate('feed');
        } catch (e) {
            this.showError('login-error', e.response?.data?.detail || 'Google Sign-In failed');
        } finally {
            document.body.classList.remove('loading');
        }
    },



    // --- Navigation ---
    showMainView() {
        document.getElementById('auth-view').classList.remove('active');
        document.getElementById('main-view').classList.add('active');
    },

    navigate(sectionId) {
        // Update Sidebar highlighting
        document.querySelectorAll('.nav-links li').forEach(el => el.classList.remove('active'));
        if (typeof event !== 'undefined' && event && event.currentTarget) {
            event.currentTarget.classList.add('active');
        } else {
            // Find manually based on text or just rely on default
            const links = document.querySelectorAll('.nav-links li');
            for (let link of links) {
                if (link.innerText.toLowerCase().includes(sectionId.toLowerCase())) {
                    link.classList.add('active');
                    break;
                }
            }
        }

        // Hide all sections
        document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));

        // Show target
        const targetRoute = `section-${sectionId}`;
        const targetEl = document.getElementById(targetRoute);
        if (targetEl) targetEl.classList.add('active');

        // Trigger loading specific data
        if (sectionId === 'feed') this.loadFeed();
        if (sectionId === 'predict') this.loadHistory();
        if (sectionId === 'search') {
            document.getElementById('search-input').value = '';
            document.getElementById('search-results-container').innerHTML = '<p class="text-muted">Type something to search...</p>';
        }
        if (sectionId === 'profile') this.fetchCurrentUser(); // refresh stats
        if (sectionId === 'notifications') this.loadNotifications();
        if (sectionId === 'chats') this.loadRecentChats();
    },

    // --- Search Logic ---
    switchSearch(type) {
        this.state.searchType = type;
        document.querySelectorAll('.search-tab').forEach(el => el.classList.remove('active'));
        if (typeof event !== 'undefined' && event && event.currentTarget) {
            event.currentTarget.classList.add('active');
        }
        this.runSearch();
    },

    async runSearch() {
        const query = document.getElementById('search-input').value.trim();
        const container = document.getElementById('search-results-container');
        if (!query) {
            container.innerHTML = '<p class="text-muted">Please enter a search term.</p>';
            return;
        }

        container.innerHTML = '<p>Searching...</p>';
        try {
            const endpoint = this.state.searchType === 'users' ? `/users/search?q=${encodeURIComponent(query)}` : `/posts/search?q=${encodeURIComponent(query)}`;
            const res = await axios.get(`${API_BASE}${endpoint}`);

            if (!res.data.length) {
                container.innerHTML = '<p class="text-muted">No results found.</p>';
                return;
            }

            if (this.state.searchType === 'users') {
                container.innerHTML = res.data.map(u => `
                    <div class="post-card" style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 12px; cursor: pointer;" onclick="app.viewUserProfile('${u.id}')">
                            <img src="${u.profile_image || `https://ui-avatars.com/api/?name=${u.name || u.username || 'A'}&background=random`}" class="avatar">
                            <div>
                                <div style="font-weight: 600; color: var(--text-color);">${u.name || 'Anonymous'}</div>
                                <div style="font-size: 13px; color: var(--primary-color);">@${u.username || 'user'}</div>
                            </div>
                        </div>
                        <button class="action-btn" onclick="app.toggleFollow('${u.id}')" style="border: 1px solid var(--primary-color); padding: 4px 12px; border-radius: 16px; ${u.is_following ? 'background: var(--primary-color); color: white;' : ''}">
                            ${u.is_following ? 'Unfollow' : 'Follow'}
                        </button>
                    </div>
                `).join('');
            } else {
                this.renderPosts(res.data, container);
            }
        } catch (e) {
            container.innerHTML = '<p class="text-muted">Search failed.</p>';
        }
    },

    async toggleFollow(targetId) {
        try {
            const res = await axios.post(`${API_BASE}/social/follow/${targetId}`);
            // Do not show an intrusive browser alert, wait for the state updates
            if (document.getElementById('section-search').classList.contains('active')) this.runSearch();
            if (document.getElementById('section-feed').classList.contains('active')) this.loadFeed();
            if (document.getElementById('section-user-profile').classList.contains('active')) this.viewUserProfile(targetId);
        } catch (e) {
            console.error('Could not toggle follow.', e);
        }
    },

    // --- Feed Logic ---
    switchFeed(type) {
        this.state.feedType = type;
        document.querySelectorAll('.feed-tabs .tab').forEach(el => el.classList.remove('active'));
        event.currentTarget.classList.add('active');
        this.loadFeed();
    },

    async loadFeed() {
        const container = document.getElementById('feed-container');
        container.innerHTML = '<p>Loading feed...</p>';
        try {
            const url = this.state.feedType === 'global' ? '/posts/feed/global' : '/posts/feed/following';
            const res = await axios.get(`${API_BASE}${url}`);
            this.renderPosts(res.data, container);
        } catch (e) {
            container.innerHTML = '<p>Failed to load feed</p>';
        }
    },

    async createPost() {
        const content = document.getElementById('post-content').value;
        if (!content.trim()) return;

        try {
            const btn = document.querySelector('.compose-actions button');
            btn.innerText = 'Posting...';
            btn.disabled = true;

            await axios.post(`${API_BASE}/posts/`, { content });
            document.getElementById('post-content').value = '';
            this.loadFeed();
        } catch (e) {
            alert('Failed to create post');
        } finally {
            const btn = document.querySelector('.compose-actions button');
            btn.innerText = 'Post';
            btn.disabled = false;
        }
    },

    async toggleLike(postId) {
        try {
            await axios.post(`${API_BASE}/posts/${postId}/like`);
            this.loadFeed(); // Lazy refresh, optimizing locally is better but this guarantees truth
        } catch (e) {
            console.error(e);
        }
    },

    renderPosts(posts, container) {
        if (!posts.length) {
            container.innerHTML = '<p class="text-muted">No posts found right now.</p>';
            return;
        }
        container.innerHTML = posts.map(post => {
            const commentsHtml = (post.comments || []).map(c => `
                <div style="font-size: 13px; margin-bottom: 8px; background: var(--bg-color); padding: 8px; border-radius: 8px;">
                    <strong style="color: var(--primary-color); cursor: pointer;" onclick="app.viewUserProfile('${c.author?.id}')">@${c.author?.username || 'user'}:</strong> ${c.content}
                </div>
            `).join('');

            return `
            <div class="post-card">
                <div class="post-header">
                    <img src="${post.author?.profile_image || `https://ui-avatars.com/api/?name=${post.author?.name || post.author?.username || 'A'}&background=random`}" class="avatar" style="cursor:pointer;" onclick="app.viewUserProfile('${post.author?.id}')">
                    <div>
                        <div class="post-author" style="cursor:pointer;" onclick="app.viewUserProfile('${post.author?.id}')">${post.author?.name || 'Anonymous'} <span style="font-weight: 500; color: var(--primary-color); font-size: 13px;">@${post.author?.username || 'user'}</span></div>
                        <div class="post-time">${new Date(post.created_at).toLocaleString()}</div>
                    </div>
                </div>
                <div class="post-content">${post.content}</div>
                <div class="post-actions">
                    <button class="action-btn" onclick="app.toggleLike(${post.id})">
                        <i>❤️</i> ${post.likes_count}
                    </button>
                    <button class="action-btn" onclick="document.getElementById('comments-${post.id}').classList.toggle('hidden')">
                        <i>💬</i> ${post.comments_count}
                    </button>
                </div>
                <!-- Comments Section -->
                <div id="comments-${post.id}" class="hidden" style="margin-top: 16px; border-top: 1px solid var(--border-color); padding-top: 12px;">
                    <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                        <input type="text" id="comment-input-${post.id}" class="input-field" placeholder="Write a comment..." style="padding: 8px;">
                        <button class="primary-btn" onclick="app.addComment(${post.id})" style="width: auto; padding: 6px 12px;">Post</button>
                    </div>
                    <div>${commentsHtml}</div>
                </div>
            </div>
        `}).join('');
    },

    async addComment(postId) {
        const input = document.getElementById(`comment-input-${postId}`);
        const content = input.value.trim();
        if (!content) return;

        try {
            await axios.post(`${API_BASE}/posts/${postId}/comments`, { content });
            input.value = '';
            // Refresh wherever we are
            if (document.getElementById('section-search').classList.contains('active')) {
                this.runSearch();
            } else {
                this.loadFeed();
            }
        } catch (e) {
            alert('Failed to post comment.');
        }
    },

    // --- AI Prediction Logic ---
    previewImage(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function (evt) {
            const img = document.getElementById('image-preview');
            img.src = evt.target.result;
            img.classList.remove('hidden');

            // Hide label text briefly
            document.querySelector('.upload-label span').innerText = 'Change Image';

            // Show Predict Button
            document.getElementById('predict-btn').classList.remove('hidden');
            document.getElementById('predict-btn').innerText = 'Scan Plant';
        }
        reader.readAsDataURL(file);
    },

    async runPrediction() {
        const fileInput = document.getElementById('image-upload');
        if (!fileInput.files[0]) return;

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const btn = document.getElementById('predict-btn');
            btn.innerText = 'Processing...';
            btn.disabled = true;

            const res = await axios.post(`${API_BASE}/predictions/`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            this.showPredictionResult(res.data);
            this.loadHistory();
        } catch (e) {
            alert('Prediction failed. Make sure it is a valid image.');
        } finally {
            const btn = document.getElementById('predict-btn');
            btn.innerText = 'Scan Plant';
            btn.disabled = false;
        }
    },

    showPredictionResult(data) {
        const card = document.getElementById('prediction-result');
        const percentage = (data.confidence * 100).toFixed(1);

        card.innerHTML = `
            <h3 style="color: ${percentage > 80 ? 'var(--primary-color)' : '#eab308'}">${data.predicted_label.replace(/_/g, ' ')}</h3>
            <p>Confidence Match: ${percentage}%</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${percentage}%"></div>
            </div>
        `;
        card.classList.remove('hidden');
    },

    async loadHistory() {
        const container = document.getElementById('prediction-history');
        try {
            const res = await axios.get(`${API_BASE}/predictions/history`);
            if (!res.data.length) {
                container.innerHTML = '<p class="text-muted">No scan history available.</p>';
                return;
            }
            container.innerHTML = res.data.map(pred => `
                <div class="history-item">
                    <img src="/static/uploads/predictions/${pred.image_path.split('/').pop()}">
                    <div style="font-weight: 600; text-transform: capitalize; font-size: 14px;">${pred.predicted_label.replace(/_/g, ' ')}</div>
                    <div style="font-size: 12px; color: var(--text-muted);">${(pred.confidence * 100).toFixed(1)}% match</div>
                </div>
            `).join('');
        } catch (e) {
            // Ignore for now
        }
    },

    // --- Notifications Logic ---
    async loadNotifications() {
        const container = document.getElementById('notifications-list');
        container.innerHTML = '<p>Loading...</p>';
        try {
            const res = await axios.get(`${API_BASE}/social/notifications`);
            if (!res.data.length) {
                container.innerHTML = '<p class="text-muted">You have no notifications.</p>';
                return;
            }
            container.innerHTML = res.data.map(notif => `
                <div class="notification-item ${notif.is_read ? 'read' : ''}">
                    <p>Someone <strong>${notif.type}d</strong> your post/profile.</p>
                    <span style="font-size: 12px; color: var(--text-muted)">${new Date(notif.created_at).toLocaleString()}</span>
                </div>
            `).join('');
        } catch (e) {
            container.innerHTML = '<p>Failed to load notifications</p>';
        }
    },

    async markAllRead() {
        try {
            await axios.put(`${API_BASE}/social/notifications/read`);
            this.loadNotifications();
        } catch (e) {
            console.error(e);
        }
    },
    // --- Public Profile Logic ---
    async viewUserProfile(userId) {
        if (!userId) return;
        if (userId === this.state.currentUser?.id) {
            this.navigate('profile');
            return;
        }

        try {
            document.body.classList.add('loading');
            const res = await axios.get(`${API_BASE}/users/${userId}`);
            const user = res.data;

            document.getElementById('public-profile-name').innerText = user.name || 'Anonymous Farmer';
            document.getElementById('public-profile-username').innerText = `@${user.username || 'user'}`;
            document.getElementById('public-profile-bio').innerText = user.bio || 'No bio available.';
            document.getElementById('public-followers-count').innerText = user.followers_count;
            document.getElementById('public-following-count').innerText = user.following_count;
            document.getElementById('public-profile-avatar').src = user.profile_image || `https://ui-avatars.com/api/?name=${user.name || user.username || 'A'}&background=random`;

            // Configure buttons
            const followBtn = document.getElementById('btn-public-follow');
            if (user.is_following) {
                followBtn.innerText = 'Unfollow';
                followBtn.style.background = 'var(--primary-color)';
                followBtn.style.color = 'white';
            } else {
                followBtn.innerText = 'Follow';
                followBtn.style.background = 'none';
                followBtn.style.color = 'var(--primary-color)';
            }
            followBtn.onclick = () => this.toggleFollow(user.id);

            const msgBtn = document.getElementById('btn-public-message');
            msgBtn.onclick = () => {
                this.navigate('chats');
                this.openChat(user.id, user.name || user.username, user.profile_image || `https://ui-avatars.com/api/?name=${user.name || user.username || 'A'}&background=random`);
            };

            // Show section
            document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));
            document.getElementById('section-user-profile').classList.add('active');

        } catch (e) {
            alert('Failed to load user profile');
        } finally {
            document.body.classList.remove('loading');
        }
    },

    // --- Chat Logic ---
    async loadRecentChats() {
        const container = document.getElementById('recent-chats-list');
        container.innerHTML = '<p class="text-muted">Loading...</p>';
        try {
            const res = await axios.get(`${API_BASE}/chat/users/recent`);
            if (!res.data.length) {
                container.innerHTML = '<p class="text-muted" style="font-size: 13px;">No recent conversations.</p>';
                return;
            }
            container.innerHTML = res.data.map(u => `
                <div class="post-card" style="display: flex; align-items: center; gap: 12px; cursor: pointer; padding: 12px; margin-bottom: 0;" onclick="app.openChat('${u.id}', '${u.name || u.username}', '${u.profile_image || `https://ui-avatars.com/api/?name=${u.name || u.username || 'A'}&background=random`}')">
                    <img src="${u.profile_image || `https://ui-avatars.com/api/?name=${u.name || u.username || 'A'}&background=random`}" class="avatar" style="width: 36px; height: 36px;">
                    <div>
                        <div style="font-weight: 600; font-size: 14px; margin-bottom: 2px;">${u.name || 'Anonymous'}</div>
                        <div style="font-size: 12px; color: var(--primary-color);">@${u.username || 'user'}</div>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            container.innerHTML = '<p class="text-muted">Failed to load recent chats.</p>';
        }
    },

    async openChat(userId, userName, userAvatar) {
        this.state.activeChatUser = userId;

        const headerName = document.getElementById('chat-active-name');
        const headerAvatar = document.getElementById('chat-active-avatar');
        const inputMsg = document.getElementById('chat-input-msg');
        const sendBtn = document.getElementById('chat-send-btn');
        const container = document.getElementById('chat-messages-container');

        headerName.innerText = userName;
        headerAvatar.src = userAvatar;
        headerAvatar.classList.remove('hidden');

        inputMsg.disabled = false;
        sendBtn.disabled = false;
        inputMsg.focus();

        container.innerHTML = '<p class="text-muted" style="text-align: center;">Loading messages...</p>';

        try {
            const res = await axios.get(`${API_BASE}/chat/${userId}`);
            if (!res.data.length) {
                container.innerHTML = '<p class="text-muted" style="text-align: center;">No messages yet. Say hi!</p>';
                return;
            }

            container.innerHTML = res.data.map(msg => {
                const isMe = msg.sender_id === this.state.currentUser?.id;
                return `
                    <div style="display: flex; flex-direction: column; align-items: ${isMe ? 'flex-end' : 'flex-start'};">
                        <div style="max-width: 70%; padding: 10px 14px; border-radius: ${isMe ? '16px 16px 4px 16px' : '16px 16px 16px 4px'}; background: ${isMe ? 'var(--primary-color)' : 'var(--bg-color)'}; color: ${isMe ? 'white' : 'var(--text-color)'}; border: ${isMe ? 'none' : '1px solid var(--border-color)'};">
                            ${msg.content}
                        </div>
                        <span style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">${new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                `;
            }).join('');

            // Auto scroll to bottom
            container.scrollTop = container.scrollHeight;

        } catch (e) {
            container.innerHTML = '<p class="text-muted" style="text-align: center;">Failed to load messages.</p>';
        }
    },

    async sendChatMessage() {
        if (!this.state.activeChatUser) return;
        const inputElem = document.getElementById('chat-input-msg');
        const content = inputElem.value.trim();
        if (!content) return;

        try {
            await axios.post(`${API_BASE}/chat/`, {
                receiver_id: this.state.activeChatUser,
                content: content
            });
            inputElem.value = '';

            // Reload active chat to show new message
            const user = document.getElementById('chat-active-name').innerText;
            const avatar = document.getElementById('chat-active-avatar').src;
            this.openChat(this.state.activeChatUser, user, avatar);

            // Reload recent chats list to bump it up
            this.loadRecentChats();

        } catch (e) {
            alert('Failed to send message');
        }
    },

    // --- Profile Editing Logic ---
    openProfileEditor() {
        if (!this.state.currentUser) return;
        const u = this.state.currentUser;

        const usernameDisplay = u.username ? `@${u.username}` : '@user';
        const nameDisplay = u.name && u.name.trim() ? u.name : '';

        // Safely map the username readout if it exists
        const editUsernameDom = document.getElementById('edit-profile-username');
        if (editUsernameDom) editUsernameDom.value = usernameDisplay;

        document.getElementById('edit-profile-name').value = nameDisplay;
        document.getElementById('edit-profile-bio').value = u.bio || '';

        const preview = document.getElementById('edit-profile-avatar-preview');
        preview.src = u.profile_image || `https://ui-avatars.com/api/?name=${u.name || u.username || 'U'}&background=random`;

        // Reset file input and base64 cache
        document.getElementById('edit-profile-avatar-input').value = '';
        this.state.pendingAvatarBase64 = null;

        document.getElementById('profile-edit-modal').classList.add('active');
    },

    closeProfileEditor() {
        document.getElementById('profile-edit-modal').classList.remove('active');
        this.state.pendingAvatarBase64 = null;
    },

    handleAvatarSelect(input) {
        if (!input.files || !input.files[0]) return;

        const file = input.files[0];

        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                const MAX_WIDTH = 400;
                const MAX_HEIGHT = 400;
                let width = img.width;
                let height = img.height;

                // Calculate ratios
                if (width > height) {
                    if (width > MAX_WIDTH) {
                        height = Math.round((height *= MAX_WIDTH / width));
                        width = MAX_WIDTH;
                    }
                } else {
                    if (height > MAX_HEIGHT) {
                        width = Math.round((width *= MAX_HEIGHT / height));
                        height = MAX_HEIGHT;
                    }
                }

                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);

                // Compress heavily into jpeg
                const compressedBase64 = canvas.toDataURL('image/jpeg', 0.6);

                document.getElementById('edit-profile-avatar-preview').src = compressedBase64;
                this.state.pendingAvatarBase64 = compressedBase64;
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    },

    async saveProfileEdits() {
        const nameEl = document.getElementById('edit-profile-name');
        const bioEl = document.getElementById('edit-profile-bio');
        const name = nameEl ? nameEl.value.trim() : '';
        const bio = bioEl ? bioEl.value.trim() : '';
        const profile_image = this.state.pendingAvatarBase64;

        const payload = {};
        if (name) payload.name = name;
        if (bio !== undefined) payload.bio = bio; // Allow empty bio to clear it
        if (profile_image) payload.profile_image = profile_image;

        try {
            document.body.classList.add('loading');

            // 1. Send the Database update request
            const res = await axios.put(`${API_BASE}/users/me`, payload);

            // 2. We received HTTP 200 OK. The DB updated successfully!
            if (res && res.data) {
                this.state.currentUser = res.data;
            }

            alert('Profile updated successfully!');

            // 3. Perform unstable DOM refreshes safely
            try {
                if (typeof this.navigate === 'function') this.navigate('profile');
                if (typeof this.closeProfileEditor === 'function') this.closeProfileEditor();
            } catch (domErr) {
                console.warn('Silenced DOM layout error during profile refresh:', domErr);
            }

        } catch (e) {
            console.error("SaveProfileEdits Error:", e);
            const msg = (e.response && e.response.data && e.response.data.detail) ? e.response.data.detail : (e.message || 'Failed to update profile');
            alert('Update Failed: ' + msg);
        } finally {
            document.body.classList.remove('loading');
            const modal = document.getElementById('profile-edit-modal');
            if (modal) modal.classList.remove('active');
        }
    },

    async fetchCurrentUser() {
        try {
            const res = await axios.get(`${API_BASE}/users/me`);
            this.state.currentUser = res.data;

            // Set User profile data
            document.getElementById('profile-name').innerText = res.data.name && res.data.name.trim() ? res.data.name : 'Anonymous Farmer';
            document.getElementById('profile-username').innerText = `@${res.data.username || 'user'}`;
            document.getElementById('profile-bio').innerText = res.data.bio || '';
            document.getElementById('followers-count').innerText = res.data.followers_count || 0;
            document.getElementById('following-count').innerText = res.data.following_count || 0;
            document.getElementById('profile-avatar').src = res.data.profile_image || `https://ui-avatars.com/api/?name=${res.data.name || res.data.username || 'A'}&background=random`;

            this.loadNotifications();
        } catch (e) {
            console.error(e);
            if (e.response?.status === 401) this.logout();
        }
    }
};

// Auto-init on load
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});

// Expose Google Callback globally
window.handleGoogleCredentialResponse = (response) => app.handleGoogleCredentialResponse(response);
