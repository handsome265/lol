import * as THREE from 'three';

class CameraRig {
  constructor(camera, player, domElement) {
    this.camera = camera;
    this.player = player;
    this.domElement = domElement;
    
    // 相機偏移(相對於玩家)
    this.offset = new THREE.Vector3(0, 2, -5);
    this.smoothness = 10.0;
    
    // 旋轉角度
    this.yaw = 0;
    this.pitch = 0.3; // 初始俯視角度
    
    // 當前相機位置
    this.currentPosition = new THREE.Vector3();
    
    console.log('✅ 相機系統已初始化');
  }

  setRotation(yaw, pitch) {
    this.yaw = yaw;
    this.pitch = pitch;
  }

  update(delta) {
    // 計算目標相機位置
    const playerPosition = this.player.position.clone();
    playerPosition.y += this.player.height * 0.9; // 看向玩家頭部

    // 根據yaw和pitch計算相機偏移
    const rotation = new THREE.Euler(this.pitch, this.yaw, 0, 'YXZ');
    const rotatedOffset = this.offset.clone().applyEuler(rotation);
    
    const targetPosition = playerPosition.clone().add(rotatedOffset);

    // 平滑插值到目標位置
    this.currentPosition.lerp(targetPosition, 1 - Math.exp(-this.smoothness * delta));
    this.camera.position.copy(this.currentPosition);

    // 看向玩家
    this.camera.lookAt(playerPosition);
  }
}

export default CameraRig;
