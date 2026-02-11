import * as THREE from 'three';

class PlayerController {
  constructor(player, camera) {
    this.player = player;
    this.camera = camera;
    this.keys = {};
    this.speed = 5.0;
    this.yaw = Math.PI; // 初始朝向前方
    this.pitch = 0.3;
    this.mouseSensitivity = 0.002;
    this.isDragging = false;

    this.bindEvents();
    console.log('✅ 控制器已初始化 - 原神模式');
  }

  bindEvents() {
    window.addEventListener('keydown', (e) => {
      this.keys[e.key.toLowerCase()] = true;
    });

    window.addEventListener('keyup', (e) => {
      this.keys[e.key.toLowerCase()] = false;
    });

    window.addEventListener('mousedown', (e) => {
      if (e.button === 0) this.isDragging = true;
    });

    window.addEventListener('mouseup', (e) => {
      if (e.button === 0) this.isDragging = false;
    });

    window.addEventListener('mousemove', (e) => {
      if (this.isDragging) {
        this.yaw -= e.movementX * this.mouseSensitivity;
        this.pitch -= e.movementY * this.mouseSensitivity;
        this.pitch = Math.max(-Math.PI / 4, Math.min(Math.PI / 4, this.pitch));
      }
    });
  }

  update(delta, cameraRig) {
    // 輸入向量 (本地空間)
    let forward = 0, right = 0;
    
    if (this.keys['w']) forward = 1;
    if (this.keys['s']) forward = -1;
    if (this.keys['a']) right = -1;
    if (this.keys['d']) right = 1;

    if (forward !== 0 || right !== 0) {
      // 關鍵修復: 基於相機 yaw 計算世界空間移動方向
      const moveX = right * Math.cos(this.yaw) + forward * Math.sin(this.yaw);
      const moveZ = right * Math.sin(this.yaw) - forward * Math.cos(this.yaw);
      
      // 歸一化
      const length = Math.sqrt(moveX * moveX + moveZ * moveZ);
      const normalizedX = moveX / length;
      const normalizedZ = moveZ / length;
      
      // 應用速度
      const targetVelX = normalizedX * this.speed;
      const targetVelZ = normalizedZ * this.speed;
      
      this.player.velocity.x = THREE.MathUtils.lerp(this.player.velocity.x, targetVelX, delta * 10);
      this.player.velocity.z = THREE.MathUtils.lerp(this.player.velocity.z, targetVelZ, delta * 10);
      
      // 角色朝向移動方向
      const angle = Math.atan2(this.player.velocity.x, this.player.velocity.z);
      this.player.mesh.rotation.y = angle;
    } else {
      this.player.velocity.x *= 0.85;
      this.player.velocity.z *= 0.85;
    }

    this.player.update(delta);
    
    if (cameraRig) {
      cameraRig.setRotation(this.yaw, this.pitch);
    }
  }
}

export default PlayerController;
