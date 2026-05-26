import { motion } from 'framer-motion'
import { pageVariants } from '../lib/motionVariants'

/**
 * Wraps a page with a restrained fade + 6px Y entrance/exit transition.
 */
export function PageTransition({ children }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="enter"
      exit="exit"
    >
      {children}
    </motion.div>
  )
}

export default PageTransition
