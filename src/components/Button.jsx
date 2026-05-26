/**
 * Button / anchor with broadcast-style variants.
 * Props: variant ("primary"|"ghost"|"destructive"), as ("button"|"a"), className, children, ...rest
 */
export function Button({ variant = 'primary', as: Tag = 'button', className = '', children, ...rest }) {
  const base = 'inline-flex items-center justify-center font-ui font-bold text-sm tracking-widest uppercase px-5 py-2.5 rounded transition-all duration-150 cursor-pointer'

  const variants = {
    primary: {
      background: 'var(--accent-red)',
      color: '#fff',
      border: '1px solid var(--accent-red)',
    },
    ghost: {
      background: 'transparent',
      color: 'var(--accent-gold)',
      border: '1px solid var(--accent-gold)',
    },
    destructive: {
      background: 'transparent',
      color: 'var(--danger)',
      border: '1px solid var(--danger)',
    },
  }

  return (
    <Tag
      className={`${base} ${className}`}
      style={variants[variant]}
      {...rest}
    >
      {children}
    </Tag>
  )
}

export default Button
