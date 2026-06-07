// 전역 유틸리티 함수들

// 로딩 표시
function showLoading() {
    const loading = document.createElement('div');
    loading.id = 'loading-overlay';
    loading.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    `;
    loading.innerHTML = `
        <div style="text-align: center; color: white;">
            <div style="font-size: 48px; animation: spin 1s linear infinite;">⚪</div>
            <p style="margin-top: 10px;">로딩 중...</p>
        </div>
    `;
    document.body.appendChild(loading);
}

function hideLoading() {
    const loading = document.getElementById('loading-overlay');
    if (loading) {
        loading.remove();
    }
}

// 알림 메시지
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// 애니메이션 추가
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// API 호출 헬퍼
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// 포켓몬 타입별 색상
const typeColors = {
    '노말': '#A8A878',
    '불꽃': '#F08030',
    '물': '#6890F0',
    '풀': '#78C850',
    '전기': '#F8D030',
    '얼음': '#98D8D8',
    '격투': '#C03028',
    '독': '#A040A0',
    '땅': '#E0C068',
    '비행': '#A890F0',
    '에스퍼': '#F85888',
    '벌레': '#A8B820',
    '바위': '#B8A038',
    '고스트': '#705898',
    '드래곤': '#7038F8',
    '악': '#705848',
    '강철': '#B8B8D0',
    '페어리': '#EE99AC'
};

// 타입 배지 생성
function createTypeBadge(type) {
    const badge = document.createElement('span');
    badge.className = 'type-badge';
    badge.textContent = type;
    badge.style.background = typeColors[type] || '#777';
    return badge;
}

// HP 바 업데이트
function updateHpBar(element, current, max) {
    const percent = Math.max(0, Math.min(100, (current / max) * 100));
    element.style.width = percent + '%';
    
    // 색상 변경
    if (percent > 50) {
        element.style.background = 'linear-gradient(90deg, #4CAF50, #8BC34A)';
    } else if (percent > 25) {
        element.style.background = 'linear-gradient(90deg, #FFC107, #FF9800)';
    } else {
        element.style.background = 'linear-gradient(90deg, #F44336, #E91E63)';
    }
}

// 경험치 계산
function calculateExpForLevel(level) {
    return level * 100;
}

function getExpProgress(currentExp, level) {
    const expNeeded = calculateExpForLevel(level);
    return (currentExp / expNeeded) * 100;
}

// 포맷팅
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// 시간 포맷
function formatTime() {
    const now = new Date();
    return now.getHours().toString().padStart(2, '0') + ':' + 
           now.getMinutes().toString().padStart(2, '0');
}

// 키보드 단축키
document.addEventListener('keydown', (e) => {
    // ESC - 뒤로 가기
    if (e.key === 'Escape') {
        const backButtons = document.querySelectorAll('.btn-back, .btn-back-main');
        if (backButtons.length > 0) {
            backButtons[0].click();
        }
    }
    
    // Enter - 첫 번째 기본 버튼 클릭
    if (e.key === 'Enter' && e.target.tagName !== 'INPUT') {
        const primaryBtn = document.querySelector('.btn-primary, .btn-continue');
        if (primaryBtn) {
            primaryBtn.click();
        }
    }
});

// 터치스크린 시뮬레이션
let touchStartX = 0;
let touchStartY = 0;

document.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
});

document.addEventListener('touchend', (e) => {
    const touchEndX = e.changedTouches[0].clientX;
    const touchEndY = e.changedTouches[0].clientY;
    
    const deltaX = touchEndX - touchStartX;
    const deltaY = touchEndY - touchStartY;
    
    // 스와이프 감지
    if (Math.abs(deltaX) > 50) {
        if (deltaX > 0) {
            // 오른쪽 스와이프 - 뒤로 가기
            const backBtn = document.querySelector('.btn-back-main');
            if (backBtn) {
                backBtn.click();
            }
        }
    }
});

// 로컬 스토리지 헬퍼
const Storage = {
    save: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Storage save error:', e);
            return false;
        }
    },
    
    load: (key, defaultValue = null) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Storage load error:', e);
            return defaultValue;
        }
    },
    
    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Storage remove error:', e);
            return false;
        }
    },
    
    clear: () => {
        try {
            localStorage.clear();
            return true;
        } catch (e) {
            console.error('Storage clear error:', e);
            return false;
        }
    }
};

// 설정 관리
const Settings = {
    load: () => Storage.load('game_settings', {
        soundEnabled: true,
        musicEnabled: true,
        textSpeed: 'normal',
        battleAnimations: true
    }),
    
    save: (settings) => Storage.save('game_settings', settings),
    
    get: (key) => {
        const settings = Settings.load();
        return settings[key];
    },
    
    set: (key, value) => {
        const settings = Settings.load();
        settings[key] = value;
        Settings.save(settings);
    }
};

// 사운드 효과 (간단한 버전)
const Sound = {
    play: (type) => {
        if (!Settings.get('soundEnabled')) return;
        
        // Web Audio API를 사용한 간단한 사운드
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        switch(type) {
            case 'click':
                oscillator.frequency.value = 800;
                gainNode.gain.value = 0.1;
                break;
            case 'success':
                oscillator.frequency.value = 1200;
                gainNode.gain.value = 0.15;
                break;
            case 'error':
                oscillator.frequency.value = 400;
                gainNode.gain.value = 0.15;
                break;
            case 'battle':
                oscillator.frequency.value = 600;
                gainNode.gain.value = 0.2;
                break;
        }
        
        oscillator.start();
        oscillator.stop(audioContext.currentTime + 0.1);
    }
};

// 버튼 클릭 사운드 추가
document.addEventListener('click', (e) => {
    if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
        Sound.play('click');
    }
});

// 디버그 모드
window.DEBUG = false;

function debug(...args) {
    if (window.DEBUG) {
        console.log('[DEBUG]', ...args);
    }
}

// 페이지 로드 완료
document.addEventListener('DOMContentLoaded', () => {
    debug('Game initialized');
    
    // 설정 로드
    const settings = Settings.load();
    debug('Settings loaded:', settings);
});

console.log('Pokemon DS Game - Main JS Loaded');