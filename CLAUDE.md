# CLAUDE.md — Instrucciones Persistentes para Chronos Quantum

## Stack Técnico de 6 Capas
1. **Capa GPU**: Three.js + `@react-three/fiber` + `@react-three/drei` (WebGPU con fallback a WebGL2).
2. **Kinetic Overlay**: GSAP + `ScrollTrigger` + Lenis Scroll para inercia natural.
3. **Post-Processing**: Bloom (intensidad 1.5), Chromatic Aberration (offset 0.002), Lens Distortion.
4. **DOM Orchestration**: Framer Motion sobre Canvas 3D (capas flotantes).
5. **Async Processing**: Web Workers (Comlink) + Howler.js para audio interactivo.
6. **Asset Pipeline**: Next.js 15 App Router + Draco Compression + Texturas KTX2.

## Reglas de Implementación y Performance
* **Fuente de Verdad Visual**: Utilizar siempre el archivo [DESIGN.md](file:///Users/robertoortega/Documents/webs/chronos-quantum/DESIGN.md) para tokens de color, fuentes, espaciados y alineación de diseño.
* **Animaciones**: **NUNCA** utilizar `useEffect` para animaciones DOM complejas ni transiciones CSS para elementos de scroll. Utilizar siempre **GSAP** y **Lenis**.
* **Importaciones de R3F/Three.js**: Importar todos los componentes de canvas dinámicamente (`next/dynamic` con `ssr: false`) para mantener el tamaño del bundle inicial JS de Next.js por debajo de los **200KB**.
* **Procesamiento de Datos**: Todo fetch o polling de APIs (fútbol, marcadores, estadísticas) debe delegarse a los Web Workers en `workers/` mediante **Comlink**. No bloquear jamás el main thread para evitar jank en el 3D.
* **Estructura TypeScript**: Mantener TypeScript en modo estricto (`strict: true`).

## Comandos Útiles
* **Desarrollo**: `npm run dev`
* **Compilación**: `npm run build`
* **Linting**: `npm run lint`
