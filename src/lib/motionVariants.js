export const pageVariants = {
  initial: { opacity: 0, y: 6 },
  enter:   { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] } },
  exit:    { opacity: 0, y: -4, transition: { duration: 0.2, ease: [0.4, 0, 1, 1] } },
}

export const scoreRevealVariants = {
  initial: { opacity: 0, y: 8, scaleY: 0.9, filter: 'blur(2px)' },
  enter:   { opacity: 1, y: 0, scaleY: 1, filter: 'blur(0px)', transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } },
}

export const lowerThirdVariants = {
  initial: { opacity: 0, y: '100%' },
  enter:   { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
}

export const staggerContainerVariants = {
  initial: {},
  enter:   { transition: { staggerChildren: 0.05, delayChildren: 0.1 } },
}

export const cardRevealVariants = {
  initial: { opacity: 0, y: 12 },
  enter:   { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
}

export const chartRevealVariants = {
  initial: { opacity: 0 },
  enter:   { opacity: 1, transition: { duration: 0.8, ease: 'easeOut' } },
}
