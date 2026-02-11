import * as THREE from 'three';

class StickmanPlayer {
  constructor(scene, collisionSystem) {
    this.scene = scene;
    this.collisionSystem = collisionSystem;
    this.height = 1.8;
    this.radius = 0.4;
    this.position = new THREE.Vector3();
    this.velocity = new THREE.Vector3();
    this.walkCycle = 0;
    this.isWalking = false;
    
    this.createStickman();
    console.log('✅ 火柴人角色已創建');
  }

  createStickman() {
    this.group = new THREE.Group();
    
    const blueMaterial = new THREE.MeshStandardMaterial({
      color: 0x2196F3,
      emissive: 0x1976D2,
      emissiveIntensity: 0.4,
      roughness: 0.3,
      metalness: 0.7
    });

    // 頭部
    const headGeo = new THREE.SphereGeometry(0.15, 32, 32);
    this.head = new THREE.Mesh(headGeo, blueMaterial);
    this.head.position.y = 1.5;
    this.head.castShadow = true;
    this.group.add(this.head);

    // 身體
    const bodyGeo = new THREE.CylinderGeometry(0.08, 0.1, 0.6, 16);
    this.body = new THREE.Mesh(bodyGeo, blueMaterial);
    this.body.position.y = 1.0;
    this.body.castShadow = true;
    this.group.add(this.body);

    // 手臂組 (左)
    this.leftArm = new THREE.Group();
    const armGeo = new THREE.CylinderGeometry(0.04, 0.035, 0.5, 12);
    this.leftUpperArm = new THREE.Mesh(armGeo, blueMaterial);
    this.leftUpperArm.position.y = -0.25;
    this.leftUpperArm.castShadow = true;
    this.leftArm.add(this.leftUpperArm);
    this.leftArm.position.set(-0.18, 1.15, 0);
    this.group.add(this.leftArm);

    // 手臂組 (右)
    this.rightArm = new THREE.Group();
    this.rightUpperArm = new THREE.Mesh(armGeo.clone(), blueMaterial);
    this.rightUpperArm.position.y = -0.25;
    this.rightUpperArm.castShadow = true;
    this.rightArm.add(this.rightUpperArm);
    this.rightArm.position.set(0.18, 1.15, 0);
    this.group.add(this.rightArm);

    // 腿部組 (左)
    this.leftLeg = new THREE.Group();
    const legGeo = new THREE.CylinderGeometry(0.05, 0.045, 0.6, 12);
    this.leftUpperLeg = new THREE.Mesh(legGeo, blueMaterial);
    this.leftUpperLeg.position.y = -0.3;
    this.leftUpperLeg.castShadow = true;
    this.leftLeg.add(this.leftUpperLeg);
    this.leftLeg.position.set(-0.08, 0.7, 0);
    this.group.add(this.leftLeg);

    // 腿部組 (右)
    this.rightLeg = new THREE.Group();
    this.rightUpperLeg = new THREE.Mesh(legGeo.clone(), blueMaterial);
    this.rightUpperLeg.position.y = -0.3;
    this.rightUpperLeg.castShadow = true;
    this.rightLeg.add(this.rightUpperLeg);
    this.rightLeg.position.set(0.08, 0.7, 0);
    this.group.add(this.rightLeg);

    this.scene.add(this.group);
    this.mesh = this.group;
  }

  setPosition(x, y, z) {
    this.position.set(x, y, z);
    this.group.position.copy(this.position);
  }

  update(delta) {
    // 應用重力
    this.velocity.y -= 9.8 * delta;
    
    // 保存舊位置
    const oldPos = this.position.clone();
    
    // 更新位置
    this.position.add(this.velocity.clone().multiplyScalar(delta));
    
    // 地面碰撞
    if (this.position.y < 0) {
      this.position.y = 0;
      this.velocity.y = 0;
    }
    
    // 檢查牆壁碰撞
    if (this.collisionSystem) {
      const pushVector = this.collisionSystem.checkCollision(this.position, this.radius);
      if (pushVector) {
        this.position.add(pushVector);
        // 停止該方向的速度
        if (Math.abs(pushVector.x) > Math.abs(pushVector.z)) {
          this.velocity.x = 0;
        } else {
          this.velocity.z = 0;
        }
      }
    }
    
    // 更新角色位置
    this.group.position.copy(this.position);
    
    // 更新行走動畫
    this.updateWalkAnimation(delta);
  }

  updateWalkAnimation(delta) {
    const speed = Math.sqrt(this.velocity.x ** 2 + this.velocity.z ** 2);
    this.isWalking = speed > 0.1;
    
    if (this.isWalking) {
      this.walkCycle += delta * 10;
      
      const legSwing = Math.sin(this.walkCycle) * 0.6;
      this.leftLeg.rotation.x = legSwing;
      this.rightLeg.rotation.x = -legSwing;
      
      this.leftArm.rotation.x = -legSwing * 0.7;
      this.rightArm.rotation.x = legSwing * 0.7;
      
      const bounce = Math.abs(Math.sin(this.walkCycle * 2)) * 0.06;
      this.body.position.y = 1.0 + bounce;
      this.head.position.y = 1.5 + bounce;
    } else {
      this.leftLeg.rotation.x *= 0.9;
      this.rightLeg.rotation.x *= 0.9;
      this.leftArm.rotation.x *= 0.9;
      this.rightArm.rotation.x *= 0.9;
      this.body.position.y = THREE.MathUtils.lerp(this.body.position.y, 1.0, delta * 5);
      this.head.position.y = THREE.MathUtils.lerp(this.head.position.y, 1.5, delta * 5);
    }
  }
}

export default StickmanPlayer;
