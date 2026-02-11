import * as THREE from 'three';

class Laboratory {
  constructor(scene) {
    this.scene = scene;
  }

  create() {
    // 創建實驗室地板標記
    const markerGeometry = new THREE.CircleGeometry(0.5, 32);
    const markerMaterial = new THREE.MeshBasicMaterial({ 
      color: 0x00ff88,
      transparent: true,
      opacity: 0.5
    });
    
    // 在不同位置創建標記點
    const positions = [
      { x: 0, z: 10 },    // 北
      { x: -8, z: 8 },    // 西北
      { x: 8, z: 8 },     // 東北
      { x: -10, z: 0 },   // 西
      { x: 10, z: 0 },    // 東
      { x: -8, z: -8 },   // 西南
      { x: 8, z: -8 },    // 東南
      { x: 0, z: -10 },   // 南
      { x: 5, z: -10 }    // 南偏右
    ];

    positions.forEach((pos, index) => {
      const marker = new THREE.Mesh(markerGeometry, markerMaterial);
      marker.rotation.x = -Math.PI / 2;
      marker.position.set(pos.x, 0.01, pos.z);
      this.scene.add(marker);

      // 添加發光立方體
      const cubeGeometry = new THREE.BoxGeometry(1, 2, 1);
      const cubeMaterial = new THREE.MeshStandardMaterial({
        color: 0x00ffff,
        emissive: 0x0088ff,
        emissiveIntensity: 0.5
      });
      const cube = new THREE.Mesh(cubeGeometry, cubeMaterial);
      cube.position.set(pos.x, 1, pos.z);
      cube.castShadow = true;
      this.scene.add(cube);
    });

    console.log('✅ 實驗室場景已創建');
  }
}

export default Laboratory;
