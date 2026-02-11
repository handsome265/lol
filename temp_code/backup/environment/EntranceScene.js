import * as THREE from 'three';

class EntranceScene {
  constructor(scene) {
    this.scene = scene;
    this.door = null;
    this.doorOpen = false;
  }

  create() {
    // 創建地面
    this.createGround();
    
    // 創建道路
    this.createPath();
    
    // 創建實驗室建築
    this.createLaboratoryBuilding();
    
    // 環境裝飾
    this.createEnvironment();
    
    console.log('✅ 入口場景已創建');
  }

  createGround() {
    // 草地
    const groundGeo = new THREE.PlaneGeometry(100, 100, 50, 50);
    const positions = groundGeo.attributes.position;
    
    // 添加起伏
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);
      const height = Math.sin(x * 0.1) * Math.cos(y * 0.1) * 0.3;
      positions.setZ(i, height);
    }
    groundGeo.computeVertexNormals();
    
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x3a5f3a,
      roughness: 0.9,
      metalness: 0.1
    });
    
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);
  }

  createPath() {
    // 石板路
    const pathGeo = new THREE.PlaneGeometry(4, 30);
    const pathMat = new THREE.MeshStandardMaterial({
      color: 0x666666,
      roughness: 0.8,
      metalness: 0.2
    });
    
    const path = new THREE.Mesh(pathGeo, pathMat);
    path.rotation.x = -Math.PI / 2;
    path.position.set(0, 0.02, 5);
    path.receiveShadow = true;
    this.scene.add(path);

    // 路邊石
    for (let i = -15; i < 20; i += 2) {
      [-2.2, 2.2].forEach(x => {
        const stoneGeo = new THREE.BoxGeometry(0.3, 0.2, 0.3);
        const stoneMat = new THREE.MeshStandardMaterial({ color: 0x888888 });
        const stone = new THREE.Mesh(stoneGeo, stoneMat);
        stone.position.set(x, 0.1, i);
        stone.castShadow = true;
        this.scene.add(stone);
      });
    }
  }

  createLaboratoryBuilding() {
    const building = new THREE.Group();
    building.position.set(0, 0, 20);

    // 主建築體
    const wallMat = new THREE.MeshStandardMaterial({
      color: 0xcccccc,
      roughness: 0.7,
      metalness: 0.3
    });

    // 左牆
    const leftWall = new THREE.Mesh(
      new THREE.BoxGeometry(0.5, 6, 15),
      wallMat
    );
    leftWall.position.set(-7.5, 3, 0);
    leftWall.castShadow = true;
    leftWall.receiveShadow = true;
    building.add(leftWall);

    // 右牆
    const rightWall = leftWall.clone();
    rightWall.position.set(7.5, 3, 0);
    building.add(rightWall);

    // 後牆
    const backWall = new THREE.Mesh(
      new THREE.BoxGeometry(15, 6, 0.5),
      wallMat
    );
    backWall.position.set(0, 3, 7.5);
    backWall.castShadow = true;
    backWall.receiveShadow = true;
    building.add(backWall);

    // 前牆 (左側)
    const frontLeftWall = new THREE.Mesh(
      new THREE.BoxGeometry(4, 6, 0.5),
      wallMat
    );
    frontLeftWall.position.set(-5.5, 3, -7.5);
    frontLeftWall.castShadow = true;
    building.add(frontLeftWall);

    // 前牆 (右側)
    const frontRightWall = frontLeftWall.clone();
    frontRightWall.position.set(5.5, 3, -7.5);
    building.add(frontRightWall);

    // 門框
    const doorFrameGeo = new THREE.BoxGeometry(4.5, 5, 0.3);
    const doorFrameMat = new THREE.MeshStandardMaterial({
      color: 0x444444,
      roughness: 0.5,
      metalness: 0.5
    });
    const doorFrame = new THREE.Mesh(doorFrameGeo, doorFrameMat);
    doorFrame.position.set(0, 2.5, -7.6);
    building.add(doorFrame);

    // 自動門 (左)
    const doorGeo = new THREE.BoxGeometry(2, 4.5, 0.2);
    const doorMat = new THREE.MeshStandardMaterial({
      color: 0x1565C0,
      roughness: 0.3,
      metalness: 0.7,
      emissive: 0x0d47a1,
      emissiveIntensity: 0.2
    });
    
    this.leftDoor = new THREE.Mesh(doorGeo, doorMat);
    this.leftDoor.position.set(-1, 2.5, -7.7);
    building.add(this.leftDoor);

    // 自動門 (右)
    this.rightDoor = this.leftDoor.clone();
    this.rightDoor.position.set(1, 2.5, -7.7);
    building.add(this.rightDoor);

    // 屋頂
    const roofGeo = new THREE.BoxGeometry(16, 0.5, 16);
    const roofMat = new THREE.MeshStandardMaterial({
      color: 0x555555,
      roughness: 0.8
    });
    const roof = new THREE.Mesh(roofGeo, roofMat);
    roof.position.set(0, 6.25, 0);
    roof.castShadow = true;
    building.add(roof);

    // 招牌
    this.createSign(building);

    this.scene.add(building);
    this.building = building;
  }

  createSign(parent) {
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');
    
    // 背景
    ctx.fillStyle = '#1565C0';
    ctx.fillRect(0, 0, 1024, 256);
    
    // 文字
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 80px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('光電實驗室', 512, 128);
    
    const texture = new THREE.CanvasTexture(canvas);
    const signMat = new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true
    });
    
    const signGeo = new THREE.PlaneGeometry(8, 2);
    const sign = new THREE.Mesh(signGeo, signMat);
    sign.position.set(0, 7, -7);
    parent.add(sign);

    // 發光效果
    const light = new THREE.PointLight(0x2196F3, 2, 10);
    light.position.set(0, 7, -6);
    parent.add(light);
  }

  createEnvironment() {
    // 添加一些樹
    for (let i = 0; i < 10; i++) {
      const angle = (i / 10) * Math.PI * 2;
      const radius = 15 + Math.random() * 10;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      this.createTree(x, z);
    }

    // 路燈
    [-3, 3].forEach(x => {
      [0, 10].forEach(z => {
        this.createStreetLight(x, z);
      });
    });
  }

  createTree(x, z) {
    const tree = new THREE.Group();

    // 樹幹
    const trunkGeo = new THREE.CylinderGeometry(0.3, 0.4, 3, 8);
    const trunkMat = new THREE.MeshStandardMaterial({ color: 0x5d4037 });
    const trunk = new THREE.Mesh(trunkGeo, trunkMat);
    trunk.position.y = 1.5;
    trunk.castShadow = true;
    tree.add(trunk);

    // 樹冠
    const foliageGeo = new THREE.SphereGeometry(2, 8, 8);
    const foliageMat = new THREE.MeshStandardMaterial({ color: 0x2e7d32 });
    const foliage = new THREE.Mesh(foliageGeo, foliageMat);
    foliage.position.y = 4;
    foliage.castShadow = true;
    tree.add(foliage);

    tree.position.set(x, 0, z);
    this.scene.add(tree);
  }

  createStreetLight(x, z) {
    const lamp = new THREE.Group();

    // 燈柱
    const poleGeo = new THREE.CylinderGeometry(0.1, 0.1, 4, 8);
    const poleMat = new THREE.MeshStandardMaterial({ color: 0x333333 });
    const pole = new THREE.Mesh(poleGeo, poleMat);
    pole.position.y = 2;
    pole.castShadow = true;
    lamp.add(pole);

    // 燈罩
    const lightGeo = new THREE.SphereGeometry(0.3, 16, 16);
    const lightMat = new THREE.MeshStandardMaterial({
      color: 0xffffcc,
      emissive: 0xffffcc,
      emissiveIntensity: 0.5
    });
    const lightBulb = new THREE.Mesh(lightGeo, lightMat);
    lightBulb.position.y = 4.2;
    lamp.add(lightBulb);

    // 點光源
    const light = new THREE.PointLight(0xffffcc, 1.5, 10);
    light.position.y = 4.2;
    light.castShadow = true;
    lamp.add(light);

    lamp.position.set(x, 0, z);
    this.scene.add(lamp);
  }

  // 檢查玩家是否靠近門
  checkDoorProximity(playerPos) {
    if (!this.building) return false;
    
    const doorPos = new THREE.Vector3(0, 0, 12.5); // 門的世界座標
    const distance = playerPos.distanceTo(doorPos);
    
    return distance < 3;
  }

  // 開門動畫
  openDoor(delta) {
    if (!this.doorOpen && this.leftDoor && this.rightDoor) {
      this.doorOpen = true;
      
      // 門的目標位置
      const targetLeft = -2.5;
      const targetRight = 2.5;
      
      // 平滑移動
      const speed = 2;
      this.leftDoor.position.x = THREE.MathUtils.lerp(
        this.leftDoor.position.x,
        targetLeft,
        delta * speed
      );
      this.rightDoor.position.x = THREE.MathUtils.lerp(
        this.rightDoor.position.x,
        targetRight,
        delta * speed
      );
    }
  }

  update(delta) {
    // 門的動畫更新可以在這裡處理
    if (this.doorOpen && this.leftDoor && this.rightDoor) {
      const targetLeft = -2.5;
      const targetRight = 2.5;
      const speed = 3;
      
      this.leftDoor.position.x = THREE.MathUtils.lerp(
        this.leftDoor.position.x,
        targetLeft,
        delta * speed
      );
      this.rightDoor.position.x = THREE.MathUtils.lerp(
        this.rightDoor.position.x,
        targetRight,
        delta * speed
      );
    }
  }
}

export default EntranceScene;
