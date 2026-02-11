import * as THREE from 'three';

class PlayerController {
  constructor(player, camera) {
    this.player = player;
    this.camera = camera;
    this.keys = {};
    this.speed = 5.0;
    this.yaw = 0;
    this.pitch = 0.3;
    this.mouseSensitivity = 0.003;
    this.isDragging = false;

    // 綁定事件
    this.bindEvents();
    
    console.log('✅ 控制器已初始化 - 完全跟隨鏡頭模式');
  }

  bindEvents() {
    // 鍵盤
    window.addEventListener('keydown', (e) => {
      this.keys[e.key.toLowerCase()] = true;
    });

    window.addEventListener('keyup', (e) => {
      this.keys[e.key.toLowerCase()] = false;
    });

    // 滑鼠
    window.addEventListener('mousedown', (e) => {
      if (e.button === 0) {
        this.isDragging = true;
      }
    });

    window.addEventListener('mouseup', (e) => {
      if (e.button === 0) {
        this.isDragging = false;
      }
    });

    window.addEventListener('mousemove', (e) => {
      if (this.isDragging) {
        this.yaw -= e.movementX * this.mouseSensitivity;
        this.pitch -= e.movementY * this.mouseSensitivity;
        this.pitch = Math.max(-Math.PI / 3, Math.min(Math.PI / 3, this.pitch));
      }
    });
  }

  update(delta, cameraRig) {
    // 獲取輸入
    const input = new THREE.Vector3();
    
    if (this.keys['w']) input.z += 1;
    if (this.keys['s']) input.z -= 1;
    if (this.keys['a']) input.x -= 1;
    if (this.keys['d']) input.x += 1;

    if (input.length() > 0) {
      input.normalize();
      
      // 關鍵修正: 完全基於相機yaw旋轉移動方向
      const moveDirection = new THREE.Vector3();
      moveDirection.x = input.x * Math.cos(this.yaw) - input.z * Math.sin(this.yaw);
      moveDirection.z = input.x * Math.sin(this.yaw) + input.z * Math.cos(this.yaw);
      
      // 應用速度
      const targetVelocity = moveDirection.multiplyScalar(this.speed);
      this.player.velocity.x = THREE.MathUtils.lerp(this.player.velocity.x, targetVelocity.x, delta * 10);
      this.player.velocity.z = THREE.MathUtils.lerp(this.player.velocity.z, targetVelocity.z, delta * 10);
      
      // 角色面向移動方向
      if (this.player.velocity.lengthSq() > 0.001) {
        const angle = Math.atan2(this.player.velocity.x, this.player.velocity.z);
        this.player.mesh.rotation.y = angle;
      }
    } else {
      // 減速
      this.player.velocity.x *= 0.85;
      this.player.velocity.z *= 0.85;
    }

    // 更新玩家
    this.player.update(delta);

    // 更新相機
    if (cameraRig) {
      cameraRig.setRotation(this.yaw, this.pitch);
    }
  }
}

export default PlayerController;
