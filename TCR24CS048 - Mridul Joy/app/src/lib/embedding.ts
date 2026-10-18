export const STATE_VARS = [
  'Order.exists',
  'Order.status_CREATED',
  'Order.status_PAID',
  'Payment.status_SUCCESS',
  'Payment.status_FAILED',
  'Notification.sent',
  'Cart.exists',
  'Cart.item_count',
  'Inventory.available',
  'User.authenticated',
  'User.role_CUSTOMER',
  'User.role_ADMIN',
];

export const DIMENSIONS = STATE_VARS.length;

// Represents a State, Goal, or condition in a vector space
export class Vector {
  values: number[];
  
  constructor(values?: number[]) {
    this.values = values || new Array(DIMENSIONS).fill(0);
  }

  static fromMap(map: Record<string, number>): Vector {
    const v = new Vector();
    STATE_VARS.forEach((key, i) => {
      if (map[key] !== undefined) {
        v.values[i] = map[key];
      }
    });
    return v;
  }

  dot(other: Vector): number {
    return this.values.reduce((sum, val, i) => sum + val * other.values[i], 0);
  }

  add(other: Vector): Vector {
    return new Vector(this.values.map((v, i) => v + other.values[i]));
  }

  sub(other: Vector): Vector {
    return new Vector(this.values.map((v, i) => v - other.values[i]));
  }

  max(other: Vector): Vector {
    return new Vector(this.values.map((v, i) => Math.max(v, other.values[i])));
  }
  
  min(other: Vector): Vector {
    return new Vector(this.values.map((v, i) => Math.min(v, other.values[i])));
  }

  relu(): Vector {
    return new Vector(this.values.map(v => Math.max(0, v)));
  }

  magnitude(): number {
    return Math.sqrt(this.dot(this));
  }

  cosineSimilarity(other: Vector): number {
    const magA = this.magnitude();
    const magB = other.magnitude();
    if (magA === 0 || magB === 0) return 0;
    return this.dot(other) / (magA * magB);
  }

  toArray(): number[] {
    return [...this.values];
  }
}

export class Capability {
  name: string;
  preconditions: Vector;
  effects: Vector;
  mask: Vector; // 1 if the capability modifies this variable, 0 otherwise
  cost: number;
  reliability: number;
  availability: number;

  constructor(
    name: string,
    preconditions: Vector,
    effects: Vector,
    mask: Vector,
    cost: number = 0,
    reliability: number = 1.0,
    availability: number = 1.0
  ) {
    this.name = name;
    this.preconditions = preconditions;
    this.effects = effects;
    this.mask = mask;
    this.cost = cost;
    this.reliability = reliability;
    this.availability = availability;
  }

  // Capability vector embedding: [Preconditions, Effects, Cost, Reliability, Availability]
  toVector(): number[] {
    return [
      ...this.preconditions.toArray(),
      ...this.effects.toArray(),
      this.cost,
      this.reliability,
      this.availability
    ];
  }
}

export function encodeState(stateMap: Record<string, number>): Vector {
  return Vector.fromMap(stateMap);
}

export function encodeGoal(goalMap: Record<string, number>): Vector {
  return Vector.fromMap(goalMap);
}

export function isCompatible(c1: Capability, c2: Capability): boolean {
  // c1 composes with c2 if c1's effects satisfy c2's preconditions
  // Specifically: C2's unmet preconditions after C1 executes must be 0
  // unmet = max(0, c2.preconditions - c1.effects)
  // For any dimension where c2 requires 1 and c1 provides 0, this is > 0.
  // Wait, if c2 requires something c1 doesn't touch, we assume it's met by the initial state?
  // Actually, compatibility usually means C1's effects *guarantee* C2's preconditions (at least the ones they share/need).
  // Strictly: The unmet dependencies that C2 needs from C1 should be 0.
  // Or: c1.effects >= c2.preconditions for the overlap.
  // Let's define compatibility as: c2.preconditions <= c1.effects (on dimensions where c2.preconditions > 0 and c1 modifies it)
  // To keep it simple: C1 is compatible with C2 if C1 provides what C2 needs.
  // We can measure incompatibility: how much of C2's preconditions are missing in C1's effects?
  // missing = c2.preconditions - c1.effects
  // We only care where missing > 0.
  const missing = c2.preconditions.sub(c1.effects).relu();
  // But wait, if C2 requires something C1 doesn't produce (like User.authenticated), it might still be compatible if the initial state has it.
  // So compatibility without state is purely based on what C1 produces vs what C2 needs.
  // If C2 has a precondition that C1 explicitly violates (e.g. C1 effect = -1 but C2 needs 1), then it's incompatible.
  // Let's define incompatibility as: there is a conflict.
  // For binary conditions (1 = true, 0 = false/don't care, -1 = explicitly false)
  // conflict = c2.preconditions * c1.effects < 0
  
  let conflict = false;
  for (let i = 0; i < DIMENSIONS; i++) {
    const p2 = c2.preconditions.values[i];
    const e1 = c1.effects.values[i];
    if (p2 > 0 && e1 < 0) conflict = true;
    if (p2 < 0 && e1 > 0) conflict = true;
  }
  
  // Also we must check if C1 provides AT LEAST ONE thing C2 needs, or if they don't conflict, they are compatible.
  // The assignment says "If the outputs and effects of C1 satisfy the inputs and preconditions of C2".
  // This implies C2 requires something C1 outputs.
  let provides = false;
  for (let i = 0; i < DIMENSIONS; i++) {
    const p2 = c2.preconditions.values[i];
    const e1 = c1.effects.values[i];
    if (p2 > 0 && e1 > 0) provides = true;
  }
  
  return !conflict && provides;
}

export function compose(c1: Capability, c2: Capability): Capability {
  // C12 = C2 o C1
  const name = `${c2.name} ◦ ${c1.name}`;
  
  // Preconditions: what C1 needs, PLUS what C2 needs that C1 didn't provide
  // p_comp = max(p1, p2 - e1)
  const p_comp = new Vector();
  for (let i = 0; i < DIMENSIONS; i++) {
    const p1 = c1.preconditions.values[i];
    const p2 = c2.preconditions.values[i];
    const e1 = c1.effects.values[i];
    // This is simple for boolean: if c1 needs it, p_comp needs it.
    // If c2 needs it and c1 doesn't provide it, p_comp needs it.
    p_comp.values[i] = Math.max(p1, p2 - Math.max(0, e1));
  }
  
  // Effects: C2's effects, PLUS C1's effects that weren't overwritten by C2
  const e_comp = new Vector();
  const m_comp = new Vector();
  for (let i = 0; i < DIMENSIONS; i++) {
    const e1 = c1.effects.values[i];
    const m1 = c1.mask.values[i];
    const e2 = c2.effects.values[i];
    const m2 = c2.mask.values[i];
    
    m_comp.values[i] = Math.max(m1, m2);
    if (m2 > 0) {
      e_comp.values[i] = e2;
    } else {
      e_comp.values[i] = e1;
    }
  }
  
  const cost = c1.cost + c2.cost;
  const reliability = c1.reliability * c2.reliability;
  const availability = Math.min(c1.availability, c2.availability);
  
  return new Capability(name, p_comp, e_comp, m_comp, cost, reliability, availability);
}

export function similarity(c1: Capability, c2: Capability): number {
  const v1 = new Vector(c1.toVector());
  const v2 = new Vector(c2.toVector());
  return v1.cosineSimilarity(v2);
}
