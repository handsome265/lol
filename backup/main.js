import * as THREE from 'three';
import StickmanPlayer from './player/StickmanPlayer.js';
import PlayerController from './player/PlayerController.js';
import CameraRig from './player/CameraRig.js';
import EntranceScene from './environment/EntranceScene.js';
import VirtualJoystick from './player/VirtualJoystick.js';

console.log('✅ Three.js 版本:', THREE.REVISION);

// 隱藏載入畫面
document.getElementById('loading').classList.add('hidden');

// 創建場景
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87CEEB); // 天空藍
scene.fog = new THREE.Fog(0x87CEEB, 30, 100);

// 創建相機
const camera = new THREE.PerspectiveCamera(
  75,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);

// 創建渲染器
const renderer = new THREE.WebGLRenderer({ 
  antialias: true,
  powerPreference: "high-performance"
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
document.getElementById('canvas-container').appendChild(renderer.domElement);

// === 光源系統 ===
// 太陽光
const sun = new THREE.DirectionalLight(0xffffff, 1.2);
sun.position.set(50, 50, 30);
sun.castShadow = true;
sun.shadow.camera.left = -50;
sun.shadow.camera.right = 50;
sun.shadow.camera.top = 50;
sun.shadow.camera.bottom = -50;
sun.shadow.camera.near = 0.1;
sun.shadow.camera.far = 150;
sun.shadow.mapSize.width = 4096;
sun.shadow.mapSize.height = 4096;
sun.shadow.bias = -0.0001;
scene.add(sun);

// 環境光
const ambient = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambient);

// 天空半球光
const hemiLight = new THREE.HemisphereLight(0x87CEEB, 0x3a5f3a, 0.5);
scene.add(hemiLight);

// 創建入口場景
const entranceScene = new EntranceScene(scene);
entranceScene.create();

// 創建火柴人角色
const player = new StickmanPlayer(scene);
player.setPosition(0, 0, -10); // 起始位置:路的開始

// 創建控制器
const playerController = new PlayerController(player, camera);

// 創建鏡頭
const cameraRig = new CameraRig(camera, player, renderer.domElement);

// 創建虛擬搖桿
const virtualJoystick = new VirtualJoystick(document.body);

// 時鐘
const clock = new THREE.Clock();

// 場景狀態
let doorTriggered = false;

// 動畫循環
function animate() {
  requestAnimationFrame(animate);
  
  const delta = clock.getDelta();
  
  // 更新控制器
  playerController.update(delta, cameraRig);
  
  // 更新鏡頭
  cameraRig.update(delta);
  
  // 更新入口場景
  entranceScene.update(delta);
  
  // 檢查門的觸發
  if (!doorTriggered && entranceScene.checkDoorProximity(player.position)) {
    console.log('🚪 靠近門,開始開門動畫');
    entranceScene.openDoor(delta);
    doorTriggered = true;
    
    // 3秒後淡出並切換場景
    setTimeout(() => {
      fadeToBlackAndSwitchScene();
    }, 2000);
  }
  
  // 渲染場景
  renderer.render(scene, camera);
}

// 淡出效果並切換場景
function fadeToBlackAndSwitchScene() {
  const overlay = document.createElement('div');
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: black;
    opacity: 0;
    transition: opacity 1s;
    z-index: 10000;
    pointer-events: none;
  `;
  document.body.appendChild(overlay);
  
  setTimeout(() => {
    overlay.style.opacity = '1';
  }, 100);
  
  setTimeout(() => {
    console.log('🔄 切換到實驗室內部場景');
    // TODO: 這裡之後會載入實驗室內部場景
    alert('即將進入實驗室內部!\n(下一階段開發中...)');
    overlay.style.opacity = '0';
    setTimeout(() => overlay.remove(), 1000);
  }, 1500);
}

// 視窗大小調整
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
});

// 開始動畫
animate();

console.log('✅ 3D場景已啟動');
console.log('🎮 操作: WASD移動(完全跟隨鏡頭) + 拖曳滑鼠旋轉視角');
console.log('🚪 向前走到實驗室門口會自動開門!');
