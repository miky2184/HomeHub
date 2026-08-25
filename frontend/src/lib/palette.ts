/** Palette di sfondo selezionabili da Impostazioni (solo --bg-page/--bg-rail:
 * card, testo e colori di categoria restano fissi per contrasto/leggibilità
 * indipendentemente dallo sfondo scelto — vedi styles/theme.css). La chiave
 * è quella salvata in AppSettings.background_theme; "" (default, non in
 * questa mappa) usa i valori base già in :root, niente override. */
export interface BackgroundTheme {
  label: string
  bgPage: string
  bgRail: string
}

export const BACKGROUND_PALETTE: Record<string, BackgroundTheme> = {
  crema: { label: 'Crema', bgPage: '#faf5ea', bgRail: '#f4ecdc' },
  salvia: { label: 'Salvia', bgPage: '#eef3e9', bgRail: '#e3ecdc' },
  cielo: { label: 'Cielo', bgPage: '#eaf1f7', bgRail: '#dee9f0' },
  rosa: { label: 'Rosa', bgPage: '#f8ecec', bgRail: '#f2e0e0' },
  lavanda: { label: 'Lavanda', bgPage: '#efecf5', bgRail: '#e6e0ef' },
  sabbia: { label: 'Sabbia', bgPage: '#f3ece0', bgRail: '#ecdfc8' },
}

export const DEFAULT_BACKGROUND_THEME = 'crema'

/** Applica lo sfondo scelto alle CSS variabili globali — "" o chiave
 * ignota ricadono silenziosamente sul default "crema" (== i valori già
 * scritti in :root, che restano lì come fallback se questo non viene mai
 * chiamato prima del primo render). */
export function applyBackgroundTheme(themeKey: string | undefined): void {
  const theme = (themeKey && BACKGROUND_PALETTE[themeKey]) || BACKGROUND_PALETTE[DEFAULT_BACKGROUND_THEME]
  const root = document.documentElement
  root.style.setProperty('--bg-page', theme.bgPage)
  root.style.setProperty('--bg-rail', theme.bgRail)
}
