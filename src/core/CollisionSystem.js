import * as THREE from 'three';

class CollisionSystem {
  constructor() {
    this.colliders = [];
  }

  addBoxCollider(position, size) {
    this.colliders.push({
      type: 'box',
      min: new THREE.Vector3(
        position.x - size.x / 2,
        position.y - size.y / 2,
        position.z - size.z / 2
      ),
      max: new THREE.Vector3(
        position.x + size.x / 2,
        position.y + size.y / 2,
        position.z + size.z / 2
      )
    });
  }

  checkCollision(position, radius = 0.4) {
    for (const collider of this.colliders) {
      if (collider.type === 'box') {
        // AABB vs Circle collision
        const closestX = Math.max(collider.min.x, Math.min(position.x, collider.max.x));
        const closestZ = Math.max(collider.min.z, Math.min(position.z, collider.max.z));
        
        const distanceX = position.x - closestX;
        const distanceZ = position.z - closestZ;
        const distanceSquared = distanceX * distanceX + distanceZ * distanceZ;
        
        if (distanceSquared < radius * radius) {
          // 計算推出向量
          const distance = Math.sqrt(distanceSquared);
          if (distance > 0) {
            const pushX = (distanceX / distance) * (radius - distance);
            const pushZ = (distanceZ / distance) * (radius - distance);
            return new THREE.Vector3(pushX, 0, pushZ);
          }
        }
      }
    }
    return null;
  }

  clear() {
    this.colliders = [];
  }
}

export default CollisionSystem;
