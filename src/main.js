import * as THREE from 'three';
import Player from './player/Player.js';
import PlayerController from './player/PlayerController.js';
import CameraRig from './player/CameraRig.js';
import Laboratory from './environment/Laboratory.js';
import VirtualJoystick from './player/VirtualJoystick.js';

console.log('✅ Three.js 版本:', THREE.REVISION);

// 隱藏載入畫面
document.getElementById('loading').classList.add('hidden');

// 創建場景
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0e27);
scene.fog = new THREE.Fog(0x0a0e27, 20, 60);

// 創建相機
const camera = new THREE.PerspectiveCamera(
  60,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);

// 創建渲染器
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
document.getElementById('canvas-container').appendChild(renderer.domElement);

// 光源
const mainLight = new THREE.DirectionalLight(0xffffff, 0.8);
mainLight.position.set(10, 20, 10);
mainLight.castShadow = true;
scene.add(mainLight);

const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
scene.add(ambientLight);

const fillLight = new THREE.DirectionalLight(0x00d4ff, 0.4);
fillLight.position.set(-10, 10, -10);
scene.add(fillLight);

// 創建地板(確保可見)
const groundGeometry = new THREE.PlaneGeometry(50, 50);
const groundMaterial = new THREE.MeshStandardMaterial({ 
  color: 0x1a1a2e,
  roughness: 0.8,
  metalness: 0.2
});
const ground = new THREE.Mesh(groundGeometry, groundMaterial);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

// 創建實驗室
const laboratory = new Laboratory(scene);
laboratory.create();

// 創建角色
const player = new Player(scene);
player.setPosition(0, 0, -15); // 起始位置:入口大廳

// 創建控制器
const playerController = new PlayerController(player, camera);

// 創建鏡頭
const cameraRig = new CameraRig(camera, player, renderer.domElement);

// 創建虛擬搖桿
const virtualJoystick = new VirtualJoystick(document.body);

// 時鐘
const clock = new THREE.Clock();

// 動畫循環
function animate() {
  requestAnimationFrame(animate);
  
  const delta = clock.getDelta();
  
  // 更新控制器
  playerController.update(delta, cameraRig);
  
  // 更新鏡頭
  if (cameraRig) {
    cameraRig.update(delta);
  }
  
  // 渲染場景
  renderer.render(scene, camera);
}

// 視窗大小調整
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// 開始動畫
animate();

console.log('✅ 3D場景已啟動');
