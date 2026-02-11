import * as THREE from 'three';

class Laboratory {
  constructor(scene) {
    this.scene = scene;
  }

  create() {
    // === 創建精緻地板 ===
    this.createFloor();
    
    // === 創建環形實驗台陣列 ===
    this.createLabStations();
    
    // === 添加環境裝飾 ===
    this.createAmbientDecor();
    
    // === 創建天空盒/背景 ===
    this.createSkybox();
    
    console.log('✅ 實驗室場景已創建');
  }

  createFloor() {
    // 主地板 - 帶紋理和細節
    const floorSize = 60;
    const floorGeometry = new THREE.PlaneGeometry(floorSize, floorSize, 50, 50);
    
    // 添加地板起伏
    const positions = floorGeometry.attributes.position;
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);
      const noise = Math.sin(x * 0.5) * Math.cos(y * 0.5) * 0.05;
      positions.setZ(i, noise);
    }
    floorGeometry.computeVertexNormals();
    
    const floorMaterial = new THREE.MeshStandardMaterial({
      color: 0x2a2a3e,
      roughness: 0.7,
      metalness: 0.3,
      envMapIntensity: 0.5
    });
    
    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    this.scene.add(floor);

    // 添加地板網格線
    const gridHelper = new THREE.GridHelper(floorSize, 40, 0x00ffff, 0x444466);
    gridHelper.material.opacity = 0.2;
    gridHelper.material.transparent = true;
    this.scene.add(gridHelper);

    // 中心發光圓環
    const ringGeometry = new THREE.RingGeometry(4, 4.5, 64);
    const ringMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.6,
      side: THREE.DoubleSide
    });
    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.02;
    this.scene.add(ring);
  }

  createLabStations() {
    // 9個實驗台位置
    const positions = [
      { x: 0, z: 12, name: '入口大廳', color: 0x4a90e2 },
      { x: -10, z: 10, name: '研究動機', color: 0xe24a90 },
      { x: 10, z: 10, name: '理論基礎', color: 0x90e24a },
      { x: -12, z: 0, name: '程式技術', color: 0xe2904a },
      { x: 12, z: 0, name: '公式推導', color: 0x4ae290 },
      { x: -10, z: -10, name: '實驗模擬', color: 0x904ae2 },
      { x: 10, z: -10, name: '數據分析', color: 0xe2e24a },
      { x: 0, z: -12, name: '結論展示', color: 0x4a4ae2 },
      { x: 6, z: -12, name: '未來展望', color: 0xe24a4a }
    ];

    positions.forEach((pos, index) => {
      this.createLabStation(pos.x, pos.z, pos.name, pos.color, index);
    });
  }

  createLabStation(x, z, name, color, index) {
    const group = new THREE.Group();
    group.position.set(x, 0, z);

    // 地板發光標記
    const markerGeometry = new THREE.CircleGeometry(1.5, 32);
    const markerMaterial = new THREE.MeshBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.3
    });
    const marker = new THREE.Mesh(markerGeometry, markerMaterial);
    marker.rotation.x = -Math.PI / 2;
    marker.position.y = 0.01;
    group.add(marker);

    // 實驗台底座
    const baseGeometry = new THREE.CylinderGeometry(1.2, 1.5, 0.3, 32);
    const baseMaterial = new THREE.MeshStandardMaterial({
      color: 0x334455,
      roughness: 0.4,
      metalness: 0.8
    });
    const base = new THREE.Mesh(baseGeometry, baseMaterial);
    base.position.y = 0.15;
    base.castShadow = true;
    base.receiveShadow = true;
    group.add(base);

    // 實驗台柱子
    const pillarGeometry = new THREE.CylinderGeometry(0.15, 0.15, 2, 16);
    const pillarMaterial = new THREE.MeshStandardMaterial({
      color: color,
      emissive: color,
      emissiveIntensity: 0.5,
      roughness: 0.3,
      metalness: 0.7
    });
    const pillar = new THREE.Mesh(pillarGeometry, pillarMaterial);
    pillar.position.y = 1.3;
    pillar.castShadow = true;
    group.add(pillar);

    // 頂部發光球體
    const sphereGeometry = new THREE.SphereGeometry(0.4, 32, 32);
    const sphereMaterial = new THREE.MeshStandardMaterial({
      color: color,
      emissive: color,
      emissiveIntensity: 1.0,
      roughness: 0.1,
      metalness: 0.9
    });
    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
    sphere.position.y = 2.5;
    sphere.castShadow = true;
    group.add(sphere);

    // 添加點光源
    const light = new THREE.PointLight(color, 2, 8);
    light.position.y = 2.5;
    light.castShadow = true;
    light.shadow.bias = -0.001;
    group.add(light);

    // 旋轉光環
    const ringCount = 3;
    for (let i = 0; i < ringCount; i++) {
      const ringGeometry = new THREE.TorusGeometry(0.6 + i * 0.2, 0.02, 16, 100);
      const ringMaterial = new THREE.MeshStandardMaterial({
        color: color,
        emissive: color,
        emissiveIntensity: 0.8,
        transparent: true,
        opacity: 0.6
      });
      const ring = new THREE.Mesh(ringGeometry, ringMaterial);
      ring.position.y = 2.5 + i * 0.15;
      ring.rotation.x = Math.PI / 2;
      group.add(ring);
      
      // 添加動畫 (稍後在 update 中處理)
      ring.userData.rotationSpeed = 0.5 + i * 0.2;
    }

    // 資訊板
    this.createInfoPanel(group, name, color);

    this.scene.add(group);
    
    // 儲存 group 以便後續動畫
    if (!this.stations) this.stations = [];
    this.stations.push(group);
  }

  createInfoPanel(parent, text, color) {
    // 創建簡單的文字面板
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');
    
    // 背景
    ctx.fillStyle = `rgba(${(color >> 16) & 255}, ${(color >> 8) & 255}, ${color & 255}, 0.8)`;
    ctx.fillRect(0, 0, 512, 128);
    
    // 文字
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 48px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 256, 64);
    
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      side: THREE.DoubleSide
    });
    
    const geometry = new THREE.PlaneGeometry(2, 0.5);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.y = 3.5;
    parent.add(mesh);
  }

  createAmbientDecor() {
    // 添加飄浮粒子
    const particleCount = 200;
    const particles = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 50;
      positions[i * 3 + 1] = Math.random() * 10;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 50;
    }
    
    particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const particleMaterial = new THREE.PointsMaterial({
      color: 0x00ffff,
      size: 0.1,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending
    });
    
    const particleSystem = new THREE.Points(particles, particleMaterial);
    this.scene.add(particleSystem);
    this.particles = particleSystem;
  }

  createSkybox() {
    // 創建漸層天空
    const skyGeometry = new THREE.SphereGeometry(100, 32, 32);
    const skyMaterial = new THREE.ShaderMaterial({
      uniforms: {
        topColor: { value: new THREE.Color(0x0a0e27) },
        bottomColor: { value: new THREE.Color(0x1a2a4a) },
        offset: { value: 33 },
        exponent: { value: 0.6 }
      },
      vertexShader: `
        varying vec3 vWorldPosition;
        void main() {
          vec4 worldPosition = modelMatrix * vec4(position, 1.0);
          vWorldPosition = worldPosition.xyz;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 topColor;
        uniform vec3 bottomColor;
        uniform float offset;
        uniform float exponent;
        varying vec3 vWorldPosition;
        void main() {
          float h = normalize(vWorldPosition + offset).y;
          gl_FragColor = vec4(mix(bottomColor, topColor, max(pow(max(h, 0.0), exponent), 0.0)), 1.0);
        }
      `,
      side: THREE.BackSide
    });
    
    const sky = new THREE.Mesh(skyGeometry, skyMaterial);
    this.scene.add(sky);
  }

  // 動畫更新方法
  update(delta) {
    // 旋轉光環
    if (this.stations) {
      this.stations.forEach(station => {
        station.children.forEach(child => {
          if (child.geometry && child.geometry.type === 'TorusGeometry') {
            child.rotation.z += child.userData.rotationSpeed * delta;
          }
        });
      });
    }
    
    // 粒子動畫
    if (this.particles) {
      this.particles.rotation.y += delta * 0.05;
    }
  }
}

export default Laboratory;
