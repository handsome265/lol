import * as THREE from 'three';

class EntranceScene {
  constructor(scene, collisionSystem) {
    this.scene = scene;
    this.collisionSystem = collisionSystem;
    this.doorOpen = false;
  }

  create() {
    this.createGround();
    this.createPath();
    this.createLaboratoryBuilding();
    this.createEnvironment();
    this.createNightSky();
    
    console.log('✅ 入口場景已創建 - 夜晚模式');
  }

  createGround() {
    // 草地
    const groundSize = 150;
    const groundGeo = new THREE.PlaneGeometry(groundSize, groundSize, 100, 100);
    const positions = groundGeo.attributes.position;
    
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);
      const height = Math.sin(x * 0.05) * Math.cos(y * 0.05) * 0.4 + 
                     Math.sin(x * 0.2) * 0.1;
      positions.setZ(i, height);
    }
    groundGeo.computeVertexNormals();
    
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x1a3a1a,
      roughness: 0.95,
      metalness: 0.05
    });
    
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);
  }

  createPath() {
    // 石板路 - 更寬更長
    const pathGeo = new THREE.PlaneGeometry(6, 40);
    const pathMat = new THREE.MeshStandardMaterial({
      color: 0x4a4a4a,
      roughness: 0.8,
      metalness: 0.1
    });
    
    const path = new THREE.Mesh(pathGeo, pathMat);
    path.rotation.x = -Math.PI / 2;
    path.position.set(0, 0.03, 0);
    path.receiveShadow = true;
    this.scene.add(path);

    // 路邊發光石塊
    for (let i = -20; i < 25; i += 3) {
      [-3.5, 3.5].forEach(x => {
        const stoneGeo = new THREE.BoxGeometry(0.4, 0.3, 0.4);
        const stoneMat = new THREE.MeshStandardMaterial({
          color: 0x88aaff,
          emissive: 0x4466ff,
          emissiveIntensity: 0.5,
          roughness: 0.3,
          metalness: 0.7
        });
        const stone = new THREE.Mesh(stoneGeo, stoneMat);
        stone.position.set(x, 0.15, i);
        stone.castShadow = true;
        this.scene.add(stone);
        
        // 發光
        const light = new THREE.PointLight(0x6688ff, 0.5, 5);
        light.position.set(x, 0.3, i);
        this.scene.add(light);
      });
    }
  }

  createLaboratoryBuilding() {
    const building = new THREE.Group();
    building.position.set(0, 0, 25);

    // 現代化材質
    const wallMat = new THREE.MeshStandardMaterial({
      color: 0xdddddd,
      roughness: 0.4,
      metalness: 0.6,
      envMapIntensity: 1.0
    });

    const glassMat = new THREE.MeshPhysicalMaterial({
      color: 0x88ccff,
      metalness: 0.1,
      roughness: 0.1,
      transmission: 0.9,
      thickness: 0.5,
      envMapIntensity: 1.5
    });

    // 主建築 - 加大尺寸
    const buildingWidth = 30;
    const buildingDepth = 25;
    const buildingHeight = 10;

    // 左牆
    const leftWall = new THREE.Mesh(
      new THREE.BoxGeometry(0.8, buildingHeight, buildingDepth),
      wallMat
    );
    leftWall.position.set(-buildingWidth / 2, buildingHeight / 2, 0);
    leftWall.castShadow = true;
    leftWall.receiveShadow = true;
    building.add(leftWall);
    
    // 碰撞體
    this.collisionSystem.addBoxCollider(
      new THREE.Vector3(-buildingWidth / 2, buildingHeight / 2, 25),
      new THREE.Vector3(0.8, buildingHeight, buildingDepth)
    );

    // 右牆
    const rightWall = leftWall.clone();
    rightWall.position.set(buildingWidth / 2, buildingHeight / 2, 0);
    building.add(rightWall);
    
    this.collisionSystem.addBoxCollider(
      new THREE.Vector3(buildingWidth / 2, buildingHeight / 2, 25),
      new THREE.Vector3(0.8, buildingHeight, buildingDepth)
    );

    // 後牆
    const backWall = new THREE.Mesh(
      new THREE.BoxGeometry(buildingWidth, buildingHeight, 0.8),
      wallMat
    );
    backWall.position.set(0, buildingHeight / 2, buildingDepth / 2);
    backWall.castShadow = true;
    building.add(backWall);
    
    this.collisionSystem.addBoxCollider(
      new THREE.Vector3(0, buildingHeight / 2, 25 + buildingDepth / 2),
      new THREE.Vector3(buildingWidth, buildingHeight, 0.8)
    );

    // 前牆左側
    const frontLeftWall = new THREE.Mesh(
      new THREE.BoxGeometry(10, buildingHeight, 0.8),
      wallMat
    );
    frontLeftWall.position.set(-10, buildingHeight / 2, -buildingDepth / 2);
    frontLeftWall.castShadow = true;
    building.add(frontLeftWall);
    
    this.collisionSystem.addBoxCollider(
      new THREE.Vector3(-10, buildingHeight / 2, 25 - buildingDepth / 2),
      new THREE.Vector3(10, buildingHeight, 0.8)
    );

    // 前牆右側
    const frontRightWall = frontLeftWall.clone();
    frontRightWall.position.set(10, buildingHeight / 2, -buildingDepth / 2);
    building.add(frontRightWall);
    
    this.collisionSystem.addBoxCollider(
      new THREE.Vector3(10, buildingHeight / 2, 25 - buildingDepth / 2),
      new THREE.Vector3(10, buildingHeight, 0.8)
    );

    // 玻璃門框
    const doorFrameGeo = new THREE.BoxGeometry(8, 8, 0.5);
    const doorFrameMat = new THREE.MeshStandardMaterial({
      color: 0x222222,
      roughness: 0.2,
      metalness: 0.9
    });
    const doorFrame = new THREE.Mesh(doorFrameGeo, doorFrameMat);
    doorFrame.position.set(0, 4, -buildingDepth / 2 - 0.2);
    building.add(doorFrame);

    // 自動玻璃門 (左)
    const doorGeo = new THREE.BoxGeometry(3.8, 7.5, 0.3);
    this.leftDoor = new THREE.Mesh(doorGeo, glassMat);
    this.leftDoor.position.set(-1.9, 4, -buildingDepth / 2 - 0.3);
    this.leftDoor.castShadow = true;
    building.add(this.leftDoor);

    // 自動玻璃門 (右)
    this.rightDoor = this.leftDoor.clone();
    this.rightDoor.position.set(1.9, 4, -buildingDepth / 2 - 0.3);
    building.add(this.rightDoor);

    // 屋頂
    const roofGeo = new THREE.BoxGeometry(buildingWidth + 2, 0.8, buildingDepth + 2);
    const roofMat = new THREE.MeshStandardMaterial({
      color: 0x333333,
      roughness: 0.6,
      metalness: 0.4
    });
    const roof = new THREE.Mesh(roofGeo, roofMat);
    roof.position.set(0, buildingHeight + 0.4, 0);
    roof.castShadow = true;
    building.add(roof);

    // 發光招牌
    this.createSign(building, buildingDepth);

    // 建築外部照明
    const buildingLights = [
      { pos: [-12, 8, -buildingDepth / 2], color: 0xffaa44 },
      { pos: [12, 8, -buildingDepth / 2], color: 0xffaa44 },
      { pos: [0, 9, -buildingDepth / 2], color: 0x44aaff }
    ];

    buildingLights.forEach(({ pos, color }) => {
      const light = new THREE.SpotLight(color, 3, 30, Math.PI / 6, 0.5);
      light.position.set(...pos);
      light.target.position.set(pos[0], 0, pos[2] - 10);
      light.castShadow = true;
      light.shadow.mapSize.width = 1024;
      light.shadow.mapSize.height = 1024;
      building.add(light);
      building.add(light.target);
    });

    this.scene.add(building);
    this.building = building;
  }

  createSign(parent, buildingDepth) {
    const canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');
    
    // 漸層背景
    const gradient = ctx.createLinearGradient(0, 0, 2048, 0);
    gradient.addColorStop(0, '#1565C0');
    gradient.addColorStop(0.5, '#0D47A1');
    gradient.addColorStop(1, '#1565C0');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 2048, 512);
    
    // 發光效果
    ctx.shadowColor = '#ffffff';
    ctx.shadowBlur = 30;
    
    // 文字
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 160px Arial, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('光電實驗室', 1024, 256);
    
    const texture = new THREE.CanvasTexture(canvas);
    const signMat = new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true
    });
    
    const signGeo = new THREE.PlaneGeometry(16, 4);
    const sign = new THREE.Mesh(signGeo, signMat);
    sign.position.set(0, 12, -buildingDepth / 2 - 0.5);
    parent.add(sign);

    // 招牌發光
    const signLight = new THREE.PointLight(0x2196F3, 5, 25);
    signLight.position.set(0, 12, -buildingDepth / 2);
    parent.add(signLight);
  }

  createEnvironment() {
    // 樹木 - 更多更密集
    for (let i = 0; i < 30; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = 20 + Math.random() * 30;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      
      // 避免擋住路
      if (Math.abs(x) > 8 || z < -15 || z > 30) {
        this.createTree(x, z);
      }
    }

    // 路燈 - 更高級
    [-4.5, 4.5].forEach(x => {
      for (let z = -15; z < 20; z += 8) {
        this.createStreetLight(x, z);
      }
    });
  }

  createTree(x, z) {
    const tree = new THREE.Group();

    // 樹幹
    const trunkGeo = new THREE.CylinderGeometry(0.4, 0.5, 4, 12);
    const trunkMat = new THREE.MeshStandardMaterial({
      color: 0x3e2723,
      roughness: 0.9
    });
    const trunk = new THREE.Mesh(trunkGeo, trunkMat);
    trunk.position.y = 2;
    trunk.castShadow = true;
    tree.add(trunk);

    // 樹冠
    const foliageGeo = new THREE.SphereGeometry(2.5, 16, 16);
    const foliageMat = new THREE.MeshStandardMaterial({
      color: 0x1b5e20,
      roughness: 0.8
    });
    const foliage = new THREE.Mesh(foliageGeo, foliageMat);
    foliage.position.y = 5;
    foliage.castShadow = true;
    tree.add(foliage);

    tree.position.set(x, 0, z);
    this.scene.add(tree);
    
    // 碰撞
    this.collisionSystem.addBoxCollider(
      new THREE.Vector3(x, 1, z),
      new THREE.Vector3(0.8, 2, 0.8)
    );
  }

  createStreetLight(x, z) {
    const lamp = new THREE.Group();

    // 燈柱
    const poleGeo = new THREE.CylinderGeometry(0.12, 0.15, 5, 16);
    const poleMat = new THREE.MeshStandardMaterial({
      color: 0x2a2a2a,
      roughness: 0.4,
      metalness: 0.8
    });
    const pole = new THREE.Mesh(poleGeo, poleMat);
    pole.position.y = 2.5;
    pole.castShadow = true;
    lamp.add(pole);

    // 燈罩
    const lightGeo = new THREE.SphereGeometry(0.4, 32, 32);
    const lightMat = new THREE.MeshStandardMaterial({
      color: 0xfff4e6,
      emissive: 0xfff4e6,
      emissiveIntensity: 1.0,
      roughness: 0.2
    });
    const lightBulb = new THREE.Mesh(lightGeo, lightMat);
    lightBulb.position.y = 5.2;
    lamp.add(lightBulb);

    // 聚光燈
    const spotLight = new THREE.SpotLight(0xfff4e6, 4, 20, Math.PI / 4, 0.5);
    spotLight.position.y = 5.2;
    spotLight.target.position.set(x, 0, z);
    spotLight.castShadow = true;
    spotLight.shadow.mapSize.width = 1024;
    spotLight.shadow.mapSize.height = 1024;
    lamp.add(spotLight);
    lamp.add(spotLight.target);

    lamp.position.set(x, 0, z);
    this.scene.add(lamp);
    
    // 碰撞
    this.collisionSystem.addBoxCollider(
      new THREE.Vector3(x, 2, z),
      new THREE.Vector3(0.3, 4, 0.3)
    );
  }

  createNightSky() {
    // 星空
    const starGeo = new THREE.BufferGeometry();
    const starCount = 3000;
    const positions = new Float32Array(starCount * 3);
    
    for (let i = 0; i < starCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 200;
      positions[i + 1] = Math.random() * 100 + 30;
      positions[i + 2] = (Math.random() - 0.5) * 200;
    }
    
    starGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const starMat = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 0.2,
      transparent: true,
      opacity: 0.8
    });
    
    const stars = new THREE.Points(starGeo, starMat);
    this.scene.add(stars);
  }

  checkDoorProximity(playerPos) {
    if (!this.building) return false;
    const doorPos = new THREE.Vector3(0, 0, 12);
    return playerPos.distanceTo(doorPos) < 4;
  }

  openDoor(delta) {
    if (!this.doorOpen) {
      this.doorOpen = true;
    }
  }

  update(delta) {
    if (this.doorOpen && this.leftDoor && this.rightDoor) {
      const targetLeft = -5;
      const targetRight = 5;
      const speed = 4;
      
      this.leftDoor.position.x = THREE.MathUtils.lerp(
        this.leftDoor.position.x, targetLeft, delta * speed
      );
      this.rightDoor.position.x = THREE.MathUtils.lerp(
        this.rightDoor.position.x, targetRight, delta * speed
      );
    }
  }
}

export default EntranceScene;
