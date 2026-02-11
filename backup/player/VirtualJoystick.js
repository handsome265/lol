class VirtualJoystick {
  constructor(container) {
    this.container = container || document.body;
    this.joystickElement = null;
    this.knobElement = null;
    this.active = false;
    this.delta = { x: 0, y: 0 };
    this.maxDistance = 50;

    // 檢測是否為觸控設備
    this.isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    if (this.isTouchDevice) {
      this.createJoystick();
      this.bindEvents();
      console.log('✅ 虛擬搖桿已啟用');
    } else {
      console.log('⚠️ 非觸控設備,虛擬搖桿未啟用');
    }
  }

  createJoystick() {
    // 創建搖桿容器
    this.joystickElement = document.createElement('div');
    this.joystickElement.style.cssText = `
      position: fixed;
      bottom: 80px;
      left: 80px;
      width: 100px;
      height: 100px;
      background: rgba(255, 255, 255, 0.1);
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      touch-action: none;
      z-index: 1000;
    `;

    // 創建搖桿旋鈕
    this.knobElement = document.createElement('div');
    this.knobElement.style.cssText = `
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 40px;
      height: 40px;
      background: rgba(255, 255, 255, 0.5);
      border: 2px solid rgba(255, 255, 255, 0.8);
      border-radius: 50%;
    `;

    this.joystickElement.appendChild(this.knobElement);
    this.container.appendChild(this.joystickElement);
  }

  bindEvents() {
    const handleStart = (e) => {
      this.active = true;
      this.updatePosition(e);
    };

    const handleMove = (e) => {
      if (this.active) {
        this.updatePosition(e);
      }
    };

    const handleEnd = () => {
      this.active = false;
      this.delta = { x: 0, y: 0 };
      this.resetKnob();
    };

    // 觸控事件
    this.joystickElement.addEventListener('touchstart', handleStart, { passive: false });
    this.joystickElement.addEventListener('touchmove', handleMove, { passive: false });
    this.joystickElement.addEventListener('touchend', handleEnd);
    this.joystickElement.addEventListener('touchcancel', handleEnd);
  }

  updatePosition(e) {
    e.preventDefault();
    
    const touch = e.touches ? e.touches[0] : e;
    const rect = this.joystickElement.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    let deltaX = touch.clientX - centerX;
    let deltaY = touch.clientY - centerY;
    
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    
    if (distance > this.maxDistance) {
      const angle = Math.atan2(deltaY, deltaX);
      deltaX = Math.cos(angle) * this.maxDistance;
      deltaY = Math.sin(angle) * this.maxDistance;
    }
    
    this.delta.x = deltaX / this.maxDistance;
    this.delta.y = deltaY / this.maxDistance;
    
    // 更新旋鈕位置
    this.knobElement.style.transform = `translate(calc(-50% + ${deltaX}px), calc(-50% + ${deltaY}px))`;
  }

  resetKnob() {
    this.knobElement.style.transform = 'translate(-50%, -50%)';
  }

  getDelta() {
    return this.delta;
  }
}

export default VirtualJoystick;
