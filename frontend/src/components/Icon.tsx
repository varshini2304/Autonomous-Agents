import type { SVGProps } from 'react'

type IconName = 'spark' | 'file' | 'download' | 'plus' | 'check' | 'clock' | 'alert' | 'arrow' | 'shield' | 'layers'

const paths: Record<IconName, string> = {
  spark: 'M12 3l1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2L12 3zm7 11l1.1 3.1L23 18l-2.9 1-1.1 3-1-3-3-1 3-1 1-3z',
  file: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zm0 2 4 4h-4zM8 13h8v1.7H8zm0 4h8v1.7H8z',
  download: 'M12 3v11m0 0 4-4m-4 4-4-4M5 17v3h14v-3',
  plus: 'M12 5v14M5 12h14',
  check: 'm5 12 4 4L19 6',
  clock: 'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zm0-16v6l4 2',
  alert: 'M12 9v4m0 4h.01M10.3 3.9 2.4 18a2 2 0 0 0 1.8 3h15.6a2 2 0 0 0 1.8-3L13.7 3.9a2 2 0 0 0-3.4 0z',
  arrow: 'M5 12h14m-6-6 6 6-6 6',
  shield: 'M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11zm-3-11 2 2 4-4',
  layers: 'm12 3 9 5-9 5-9-5 9-5zm-9 9 9 5 9-5m-18 5 9 5 9-5',
}

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName
}

export default function Icon({ name, ...props }: IconProps) {
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...props}><path d={paths[name]} /></svg>
}
