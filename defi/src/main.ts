import Phaser from 'phaser'
import './style.css'
import { ROUND_SECONDS, STARTING_LIVES, TARGET_STARS, touchesCircle } from './game/rules'

type Direction = 'up' | 'down' | 'left' | 'right'
type GameStatus = 'ready' | 'playing' | 'won' | 'lost'

interface MovingCircle {
  x: number
  y: number
  radius: number
  speedX: number
  speedY: number
  object: Phaser.GameObjects.Shape
  halo?: Phaser.GameObjects.Arc
  phase: number
}

class CosmoScene extends Phaser.Scene {
  private player!: Phaser.GameObjects.Container
  private stars: MovingCircle[] = []
  private asteroids: MovingCircle[] = []
  private keys!: Record<string, Phaser.Input.Keyboard.Key>
  private heldDirections = new Set<Direction>()
  private status: GameStatus = 'ready'
  private score = 0
  private lives = STARTING_LIVES
  private secondsLeft = ROUND_SECONDS
  private elapsed = 0
  private hitCooldown = 0
  private playerX = 480
  private playerY = 320
  private readonly fieldWidth = 960
  private readonly fieldHeight = 640
  private onStartEvent = () => this.startRound()

  constructor() {
    super('cosmo')
  }

  create() {
    this.drawBackdrop()
    this.createPlayer()
    this.createStars()
    this.createAsteroids()
    this.keys = this.input.keyboard!.addKeys('W,A,S,D,UP,DOWN,LEFT,RIGHT') as Record<string, Phaser.Input.Keyboard.Key>
    window.addEventListener('cosmo:start', this.onStartEvent)
    window.addEventListener('cosmo:restart', this.onStartEvent)
    window.addEventListener('cosmo:direction', this.onDirection as EventListener)
    window.addEventListener('cosmo:release-all', this.releaseDirections)
    window.addEventListener('resize', this.redrawBackdrop)
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      window.removeEventListener('cosmo:start', this.onStartEvent)
      window.removeEventListener('cosmo:restart', this.onStartEvent)
      window.removeEventListener('cosmo:direction', this.onDirection as EventListener)
      window.removeEventListener('cosmo:release-all', this.releaseDirections)
      window.removeEventListener('resize', this.redrawBackdrop)
    })
    this.emitHud()
  }

  private drawBackdrop = () => {
    if (!this.children) return
    const old = this.children.getByName('backdrop')
    old?.destroy()
    const graphics = this.add.graphics().setName('backdrop')
    graphics.fillStyle(0x0b1024, 1).fillRect(0, 0, this.fieldWidth, this.fieldHeight)
    graphics.fillStyle(0x171d3e, 0.5).fillCircle(125, 540, 165)
    graphics.fillStyle(0x4d447e, 0.14).fillCircle(790, 95, 180)
    let seed = 449
    for (let i = 0; i < 110; i += 1) {
      seed = (seed * 16807) % 2147483647
      const x = (seed / 2147483647) * this.fieldWidth
      seed = (seed * 16807) % 2147483647
      const y = (seed / 2147483647) * this.fieldHeight
      const radius = i % 13 === 0 ? 2 : 0.8 + (i % 3) * 0.35
      graphics.fillStyle(i % 9 === 0 ? 0xa99bff : 0xe3e8ff, i % 4 === 0 ? 0.75 : 0.35)
      graphics.fillCircle(x, y, radius)
    }
    graphics.lineStyle(1, 0x8991c7, 0.1).strokeCircle(480, 320, 230)
    graphics.lineStyle(1, 0x8991c7, 0.07).strokeCircle(480, 320, 310)
    graphics.setDepth(-5)
  }

  private redrawBackdrop = () => this.drawBackdrop()

  private createPlayer() {
    const glow = this.add.circle(0, 0, 25, 0x8da0ff, 0.12)
    const body = this.add.triangle(0, 0, 0, -20, 15, 14, -15, 14, 0xe8ff8a)
      .setStrokeStyle(2, 0xffffff, 0.8)
    const window = this.add.circle(0, -1, 5, 0x8de1ee)
    const flame = this.add.triangle(0, 17, 0, -7, 5, 6, -5, 6, 0xff9a71, 0.95)
    this.player = this.add.container(this.playerX, this.playerY, [glow, flame, body, window]).setDepth(3)
  }

  private createStars() {
    this.stars = []
    for (let index = 0; index < TARGET_STARS; index += 1) {
      const x = 80 + ((index * 127 + 38) % 800)
      const y = 90 + ((index * 197 + 74) % 460)
      const star = this.add.star(x, y, 5, 7, 15, 0xe8ff8a)
        .setStrokeStyle(1, 0xffffff, 0.9).setDepth(2)
      const halo = this.add.circle(x, y, 20, 0xe8ff8a, 0.07).setDepth(1)
      this.stars.push({ x, y, radius: 17, speedX: 0, speedY: 0, object: star, halo, phase: index * 1.2 })
    }
  }

  private createAsteroids() {
    const locations = [
      { x: 245, y: 195, r: 24, vx: 31, vy: 23 },
      { x: 702, y: 184, r: 18, vx: -26, vy: 36 },
      { x: 385, y: 465, r: 21, vx: 35, vy: -27 },
      { x: 785, y: 435, r: 26, vx: -32, vy: -22 },
      { x: 515, y: 125, r: 15, vx: 23, vy: 32 },
    ]
    this.asteroids = locations.map(({ x, y, r, vx, vy }, index) => {
      const rock = this.add.circle(x, y, r, index % 2 === 0 ? 0x777d9b : 0x626987)
        .setStrokeStyle(2, 0xa9adc0, 0.75).setDepth(2)
      const crater = this.add.circle(x - r * 0.2, y - r * 0.2, r * 0.27, 0x343b5b, 0.65).setDepth(2)
      rock.setData('crater', crater)
      return { x, y, radius: r + 3, speedX: vx, speedY: vy, object: rock, phase: 0 }
    })
  }

  private onDirection = (event: CustomEvent<{ direction: Direction; active: boolean }>) => {
    if (event.detail.active) this.heldDirections.add(event.detail.direction)
    else this.heldDirections.delete(event.detail.direction)
  }

  private releaseDirections = () => this.heldDirections.clear()

  private startRound() {
    this.status = 'playing'
    this.score = 0
    this.lives = STARTING_LIVES
    this.secondsLeft = ROUND_SECONDS
    this.elapsed = 0
    this.hitCooldown = 0
    this.playerX = 480
    this.playerY = 320
    this.player.setPosition(this.playerX, this.playerY).setAlpha(1)
    this.stars.forEach((star) => {
      star.object.setVisible(true).setPosition(star.x, star.y).setScale(1)
      star.halo?.setVisible(true).setPosition(star.x, star.y).setScale(1)
    })
    this.emitHud()
    this.announceState('playing')
  }

  update(_time: number, deltaMs: number) {
    if (this.status !== 'playing') return
    const dt = Math.min(deltaMs / 1000, 0.04)
    this.elapsed += dt
    this.hitCooldown = Math.max(0, this.hitCooldown - dt)
    this.secondsLeft = Math.max(0, ROUND_SECONDS - Math.floor(this.elapsed))
    this.animateObjects(this.elapsed, dt)

    let horizontal = 0
    let vertical = 0
    if (this.keys.LEFT.isDown || this.keys.A.isDown || this.heldDirections.has('left')) horizontal -= 1
    if (this.keys.RIGHT.isDown || this.keys.D.isDown || this.heldDirections.has('right')) horizontal += 1
    if (this.keys.UP.isDown || this.keys.W.isDown || this.heldDirections.has('up')) vertical -= 1
    if (this.keys.DOWN.isDown || this.keys.S.isDown || this.heldDirections.has('down')) vertical += 1
    if (horizontal !== 0 || vertical !== 0) {
      const length = Math.hypot(horizontal, vertical)
      this.playerX += (horizontal / length) * 255 * dt
      this.playerY += (vertical / length) * 255 * dt
      this.player.setRotation(Math.atan2(vertical, horizontal) + Math.PI / 2)
    }
    this.playerX = Phaser.Math.Clamp(this.playerX, 34, this.fieldWidth - 34)
    this.playerY = Phaser.Math.Clamp(this.playerY, 46, this.fieldHeight - 38)
    this.player.setPosition(this.playerX, this.playerY)

    for (const star of this.stars) {
      if (!star.object.visible) continue
      if (touchesCircle(this.playerX, this.playerY, 15, star.x, star.y, 10)) {
        star.object.setVisible(false)
        star.halo?.setVisible(false)
        this.score += 1
        this.emitHud()
        this.cameras.main.shake(90, 0.002)
        if (this.score >= TARGET_STARS) return this.finish(true)
      }
    }

    if (this.hitCooldown <= 0) {
      for (const asteroid of this.asteroids) {
        if (touchesCircle(this.playerX, this.playerY, 15, asteroid.x, asteroid.y, asteroid.radius)) {
          this.lives -= 1
          this.hitCooldown = 1.15
          this.cameras.main.shake(180, 0.005)
          this.tweens.add({ targets: this.player, alpha: 0.25, yoyo: true, repeat: 3, duration: 85 })
          this.emitHud()
          if (this.lives <= 0) return this.finish(false)
          break
        }
      }
    }
    if (this.secondsLeft <= 0) this.finish(false)
    else this.emitTimer()
  }

  private animateObjects(time: number, dt: number) {
    this.stars.forEach((star, index) => {
      star.phase += 0.035
      star.object.setRotation(star.phase).setScale(1 + Math.sin(time * 3 + index) * 0.1)
      star.halo?.setScale(0.85 + (Math.sin(time * 2 + index) + 1) * 0.13)
    })
    this.asteroids.forEach((rock) => {
      rock.x += rock.speedX * dt
      rock.y += rock.speedY * dt
      if (rock.x < 55 || rock.x > this.fieldWidth - 55) rock.speedX *= -1
      if (rock.y < 55 || rock.y > this.fieldHeight - 55) rock.speedY *= -1
      rock.object.setPosition(rock.x, rock.y).setRotation(rock.object.rotation + 0.006)
      const crater = rock.object.getData('crater') as Phaser.GameObjects.Arc
      crater?.setPosition(rock.x - rock.radius * 0.28, rock.y - rock.radius * 0.28)
    })
  }

  private finish(won: boolean) {
    this.status = won ? 'won' : 'lost'
    this.announceState(this.status)
  }

  private emitHud() {
    document.querySelector('#score')!.innerHTML = `${String(this.score).padStart(2, '0')} <small>/ ${TARGET_STARS}</small>`
    document.querySelector('#lives')!.textContent = Array.from({ length: STARTING_LIVES }, (_, i) => i < this.lives ? '♥' : '·').join(' ')
    this.emitTimer()
  }

  private emitTimer() {
    const timer = document.querySelector('#timer')
    if (timer) timer.innerHTML = `${String(this.secondsLeft).padStart(2, '0')}<span>s</span>`
  }

  private announceState(status: GameStatus) {
    window.dispatchEvent(new CustomEvent('cosmo:state', { detail: { status, score: this.score } }))
  }
}

const game = new Phaser.Game({
  type: Phaser.AUTO,
  parent: 'game',
  width: 960,
  height: 640,
  backgroundColor: '#0b1024',
  scene: [CosmoScene],
  scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
  render: { antialias: true, pixelArt: false },
  input: { activePointers: 3 },
})

const overlay = document.querySelector<HTMLElement>('#overlay')!
const hud = document.querySelector<HTMLElement>('#hud')!
const title = document.querySelector<HTMLElement>('#overlay-title')!
const copy = document.querySelector<HTMLElement>('#overlay-copy')!
const eyebrow = document.querySelector<HTMLElement>('#overlay-eyebrow')!
const icon = document.querySelector<HTMLElement>('#overlay-icon')!
const startButton = document.querySelector<HTMLButtonElement>('#start-button')!

startButton.addEventListener('click', () => {
  const eventName = overlay.dataset.status === 'won' || overlay.dataset.status === 'lost'
    ? 'cosmo:restart'
    : 'cosmo:start'
  window.dispatchEvent(new Event(eventName))
})

window.addEventListener('cosmo:state', ((event: CustomEvent<{ status: GameStatus; score: number }>) => {
  const { status, score } = event.detail
  overlay.dataset.status = status
  const isPlaying = status === 'playing'
  overlay.classList.toggle('is-hidden', isPlaying)
  hud.classList.toggle('is-visible', isPlaying)
  if (status === 'won') {
    eyebrow.textContent = 'MISSION ACCOMPLIE'
    icon.textContent = '✦'
    title.innerHTML = 'Bien joué,<br /><em>astronaute !</em>'
    copy.innerHTML = `Tu as ramené les ${TARGET_STARS} étoiles à bon port.<br />Le cosmos te remercie.`
    startButton.innerHTML = 'Rejouer la mission <span>↗</span>'
  } else if (status === 'lost') {
    eyebrow.textContent = 'MISSION TERMINÉE'
    icon.textContent = '☄'
    title.innerHTML = 'On retente<br /><em>le voyage ?</em>'
    copy.innerHTML = `Tu as récupéré ${score} étoile${score > 1 ? 's' : ''}.<br />Une nouvelle orbite t’attend.`
    startButton.innerHTML = 'Réessayer <span>↗</span>'
  }
}) as EventListener)

document.querySelectorAll<HTMLButtonElement>('.pad-button').forEach((button) => {
  const direction = button.dataset.dir as Direction
  const setActive = (active: boolean) => window.dispatchEvent(new CustomEvent('cosmo:direction', { detail: { direction, active } }))
  button.addEventListener('pointerdown', (event) => { event.preventDefault(); button.setPointerCapture(event.pointerId); setActive(true) })
  button.addEventListener('pointerup', () => setActive(false))
  button.addEventListener('pointercancel', () => setActive(false))
  button.addEventListener('lostpointercapture', () => setActive(false))
})
window.addEventListener('blur', () => window.dispatchEvent(new Event('cosmo:release-all')))
