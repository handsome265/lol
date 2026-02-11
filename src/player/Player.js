import * as THREE from 'three';

class Player {
  constructor(scene) {
    this.scene = scene;
    this.height = 1.8;
    this.radius = 0.4;
    this.velocity = new THREE.Vector3();
    this.position = new THREE.Vector3();

    // 創建玩家網格(簡單的膠囊體)
    const geometry = new THREE.CapsuleGeometry(this.radius, this.height - this.radius * 2, 8, 16);
    const material = new THREE.MeshStandardMaterial({ 
      color: 0xff6600,
      emissive: 0xff3300,
      emissiveIntensity: 0.3
    });
    
    this.mesh = new THREE.Mesh(geometry, material);
    this.mesh.castShadow = true;
    this.mesh.receiveShadow = true;
    
    scene.add(this.mesh);
    
    console.log('✅ 玩家已創建');
  }

  setPosition(x, y, z) {
    this.position.set(x, y, z);
    this.mesh.position.copy(this.position);
    this.mesh.position.y += this.height / 2; // 調整高度
  }

  update(delta) {
    // 應用重力
    this.velocity.y -= 9.8 * delta;
    
    // 更新位置
    this.position.add(this.velocity.clone().multiplyScalar(delta));
    
    // 地面碰撞
    if (this.position.y < 0) {
      this.position.y = 0;
      this.velocity.y = 0;
    }
    
    // 更新網格位置
    this.mesh.position.copy(this.position);
    this.mesh.position.y += this.height / 2;
  }
}

export default Player;
