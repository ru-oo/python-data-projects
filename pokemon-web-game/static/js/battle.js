// 배틀 시스템

class BattleSystem {
    constructor() {
        this.state = {
            phase: 'select', // select, attack, result
            turn: 'player',
            animations: []
        };
    }
    
    // 데미지 계산 (클라이언트 사이드 예측용)
    calculateDamage(attacker, defender, move) {
        let damage = 0;
        
        if (move.category === 'physical') {
            damage = (attacker.attack / defender.defense) * move.power * 0.4;
        } else if (move.category === 'special') {
            damage = (attacker.sp_attack / defender.sp_defense) * move.power * 0.4;
        }
        
        // 랜덤 요소
        const variance = Math.random() * 0.2 - 0.1; // -10% ~ +10%
        damage = damage * (1 + variance);
        
        // 최소 1 데미지
        return Math.max(1, Math.floor(damage));
    }
    
    // 타입 상성 계산
    getTypeEffectiveness(attackType, defenderType1, defenderType2) {
        const effectiveness = {
            '불꽃': { '풀': 2, '얼음': 2, '벌레': 2, '강철': 2, '불꽃': 0.5, '물': 0.5, '바위': 0.5, '드래곤': 0.5 },
            '물': { '불꽃': 2, '땅': 2, '바위': 2, '물': 0.5, '풀': 0.5, '드래곤': 0.5 },
            '풀': { '물': 2, '땅': 2, '바위': 2, '불꽃': 0.5, '풀': 0.5, '독': 0.5, '비행': 0.5, '벌레': 0.5, '드래곤': 0.5, '강철': 0.5 },
            '전기': { '물': 2, '비행': 2, '전기': 0.5, '풀': 0.5, '드래곤': 0.5, '땅': 0 },
            '얼음': { '풀': 2, '땅': 2, '비행': 2, '드래곤': 2, '불꽃': 0.5, '물': 0.5, '얼음': 0.5, '강철': 0.5 },
            '격투': { '노말': 2, '얼음': 2, '바위': 2, '악': 2, '강철': 2, '독': 0.5, '비행': 0.5, '에스퍼': 0.5, '벌레': 0.5, '페어리': 0.5, '고스트': 0 },
            '독': { '풀': 2, '페어리': 2, '독': 0.5, '땅': 0.5, '바위': 0.5, '고스트': 0.5, '강철': 0 },
            '땅': { '불꽃': 2, '전기': 2, '독': 2, '바위': 2, '강철': 2, '풀': 0.5, '벌레': 0.5, '비행': 0 },
            '비행': { '풀': 2, '격투': 2, '벌레': 2, '전기': 0.5, '바위': 0.5, '강철': 0.5 },
            '에스퍼': { '격투': 2, '독': 2, '에스퍼': 0.5, '강철': 0.5, '악': 0 },
            '벌레': { '풀': 2, '에스퍼': 2, '악': 2, '불꽃': 0.5, '격투': 0.5, '독': 0.5, '비행': 0.5, '고스트': 0.5, '강철': 0.5, '페어리': 0.5 },
            '바위': { '불꽃': 2, '얼음': 2, '비행': 2, '벌레': 2, '격투': 0.5, '땅': 0.5, '강철': 0.5 },
            '고스트': { '에스퍼': 2, '고스트': 2, '악': 0.5, '노말': 0 },
            '드래곤': { '드래곤': 2, '강철': 0.5, '페어리': 0 },
            '악': { '에스퍼': 2, '고스트': 2, '격투': 0.5, '악': 0.5, '페어리': 0.5 },
            '강철': { '얼음': 2, '바위': 2, '페어리': 2, '불꽃': 0.5, '물': 0.5, '전기': 0.5, '강철': 0.5 },
            '페어리': { '격투': 2, '드래곤': 2, '악': 2, '불꽃': 0.5, '독': 0.5, '강철': 0.5 }
        };
        
        let multiplier = 1;
        
        if (effectiveness[attackType]) {
            if (effectiveness[attackType][defenderType1]) {
                multiplier *= effectiveness[attackType][defenderType1];
            }
            if (defenderType2 && effectiveness[attackType][defenderType2]) {
                multiplier *= effectiveness[attackType][defenderType2];
            }
        }
        
        return multiplier;
    }
    
    // 애니메이션
    playAttackAnimation(attackerElement, defenderElement, moveType) {
        return new Promise((resolve) => {
            // 공격자 애니메이션
            attackerElement.style.transition = 'transform 0.15s';
            attackerElement.style.transform = 'translateX(-20px)';
            
            setTimeout(() => {
                attackerElement.style.transform = 'translateX(0)';
                
                // 피격 애니메이션
                defenderElement.style.transition = 'all 0.2s';
                defenderElement.style.filter = 'brightness(0.5)';
                
                // 타입별 이펙트 색상
                const effectColor = {
                    '불꽃': '#ff6b6b',
                    '물': '#4ecdc4',
                    '풀': '#95e1d3',
                    '전기': '#f9ca24',
                    '노말': '#95a5a6'
                };
                
                const color = effectColor[moveType] || '#ffffff';
                this.createHitEffect(defenderElement, color);
                
                setTimeout(() => {
                    defenderElement.style.filter = 'brightness(1)';
                    resolve();
                }, 200);
            }, 150);
        });
    }
    
    createHitEffect(element, color) {
        const effect = document.createElement('div');
        effect.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 100px;
            height: 100px;
            background: radial-gradient(circle, ${color} 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
            animation: hitEffect 0.4s ease-out;
        `;
        
        element.parentElement.style.position = 'relative';
        element.parentElement.appendChild(effect);
        
        setTimeout(() => effect.remove(), 400);
    }
    
    // HP 바 애니메이션
    animateHpBar(hpBarElement, fromPercent, toPercent, duration = 500) {
        return new Promise((resolve) => {
            const startTime = Date.now();
            const startPercent = fromPercent;
            const diffPercent = toPercent - fromPercent;
            
            const animate = () => {
                const elapsed = Date.now() - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                const currentPercent = startPercent + (diffPercent * progress);
                hpBarElement.style.width = currentPercent + '%';
                
                // 색상 변경
                if (currentPercent > 50) {
                    hpBarElement.style.background = 'linear-gradient(90deg, #4CAF50, #8BC34A)';
                } else if (currentPercent > 25) {
                    hpBarElement.style.background = 'linear-gradient(90deg, #FFC107, #FF9800)';
                } else {
                    hpBarElement.style.background = 'linear-gradient(90deg, #F44336, #E91E63)';
                }
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    resolve();
                }
            };
            
            animate();
        });
    }
    
    // 포획 애니메이션
    playCatchAnimation(pokemonElement) {
        return new Promise((resolve) => {
            const pokeball = document.createElement('div');
            pokeball.innerHTML = '⚾';
            pokeball.style.cssText = `
                position: absolute;
                font-size: 40px;
                bottom: 20px;
                left: 20px;
                transition: all 0.5s ease-in;
            `;
            
            pokemonElement.parentElement.appendChild(pokeball);
            
            // 던지기
            setTimeout(() => {
                const rect = pokemonElement.getBoundingClientRect();
                pokeball.style.left = (rect.left - 20) + 'px';
                pokeball.style.bottom = (window.innerHeight - rect.top - 40) + 'px';
                pokeball.style.transform = 'rotate(720deg)';
            }, 100);
            
            // 흔들림
            setTimeout(() => {
                pokeball.style.animation = 'shake 0.5s ease 3';
            }, 600);
            
            setTimeout(() => {
                pokeball.remove();
                resolve();
            }, 2100);
        });
    }
    
    // 경험치 획득 애니메이션
    showExpGain(amount, element) {
        const expText = document.createElement('div');
        expText.textContent = `+${amount} EXP`;
        expText.style.cssText = `
            position: absolute;
            color: #f39c12;
            font-weight: bold;
            font-size: 24px;
            animation: floatUp 2s ease-out forwards;
            pointer-events: none;
        `;
        
        element.appendChild(expText);
        
        setTimeout(() => expText.remove(), 2000);
    }
    
    // 레벨업 이펙트
    showLevelUpEffect(element) {
        const effect = document.createElement('div');
        effect.innerHTML = '⭐ LEVEL UP! ⭐';
        effect.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #f39c12;
            font-weight: bold;
            font-size: 32px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            animation: pulse 0.5s ease 3;
            pointer-events: none;
            z-index: 1000;
        `;
        
        element.style.position = 'relative';
        element.appendChild(effect);
        
        setTimeout(() => effect.remove(), 1500);
    }
}

// 애니메이션 CSS 추가
const battleStyle = document.createElement('style');
battleStyle.textContent = `
    @keyframes hitEffect {
        0% {
            transform: translate(-50%, -50%) scale(0);
            opacity: 1;
        }
        100% {
            transform: translate(-50%, -50%) scale(2);
            opacity: 0;
        }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px) rotate(-5deg); }
        75% { transform: translateX(10px) rotate(5deg); }
    }
    
    @keyframes floatUp {
        0% {
            transform: translateY(0);
            opacity: 1;
        }
        100% {
            transform: translateY(-50px);
            opacity: 0;
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: translate(-50%, -50%) scale(1);
        }
        50% {
            transform: translate(-50%, -50%) scale(1.2);
        }
    }
`;
document.head.appendChild(battleStyle);

// 전역 배틀 시스템 인스턴스
window.battleSystem = new BattleSystem();

console.log('Battle System Loaded');