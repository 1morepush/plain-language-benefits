/*
 * i18n.js — every piece of text the website itself says, in English and Spanish.
 * (Question wording and explanations are NOT here. They come from the data files.)
 */
const STRINGS = {
  en: {
    skip: "Skip to main content",
    tagline: "An AI helper for understanding unemployment forms",
    langLabel: "Language",
    disclaimer:
      "Plain Path is a student prototype, not legal advice and not affiliated with Arizona DES.",
    loading: "Loading…",
    loadError: "Plain Path could not load. Please refresh the page.",

    welcomeTitle: "Welcome to Plain Path",
    welcomeIntro:
      "Plain Path explains the questions on the Arizona unemployment insurance application in plain language. It is a reading aid only.",
    doesTitle: "What it does",
    does1: "Shows the official wording of each question, exactly as written.",
    does2: "Explains each question in plain language.",
    does3: "Lists what you will need to answer it.",
    does4: "Tells you when it is best to check with a person.",
    doesNotTitle: "What it does not do",
    doesNot1: "It does not fill out or send your application.",
    doesNot2: "It does not tell you if you will get benefits.",
    doesNot3: "It does not tell you what to answer. Your answers must be your own and must be true.",
    doesNot4: "It does not ask for or keep your name, Social Security number, or any personal details.",
    start: "Start",

    intakeTitle: "A few quick questions",
    intakeIntro:
      "These yes or no questions only decide which parts of the walkthrough you see. They are not sent anywhere and they do not decide if you can get benefits.",
    yes: "Yes",
    no: "No",
    intakeError: "Please answer every question to continue.",
    back: "Back",
    next: "Continue",

    docsTitle: "Pause and gather your documents",
    docsIntro:
      "The form is easier with your papers next to you. Tick each item as you find it. The ticks are only a reminder for you and stay on this device.",
    docsContinue: "I'm ready. Show me the form questions",

    progressTitle: "Your progress",
    stepOf: "Section {n} of {total}",
    statusDone: "done",
    statusCurrent: "you are here",
    statusTodo: "not started",
    questionN: "Question {n}",
    officialLabel: "Official wording",
    officialOnlyEnglish: "The official wording is only available in English.",
    plainLabel: "In plain words",
    needLabel: "What you'll need",
    comingSoon: "Explanation coming soon. See official instructions.",
    checkTitle: "Check with a person",
    checkDefault:
      "This question can affect your claim. Before you answer, it is a good idea to talk with the agency or with legal aid. They can help for free.",
    callLabel: "Call",
    sourceLabel: "Source",
    notListed:
      "Is a question on your form not shown here? Plain Path cannot help with that question yet. Please use the official instructions.",
    noQuestions: "There are no questions in this section yet.",
    prevSection: "Previous section",
    nextSection: "Next section",
    finish: "Finish",

    askTitle: "Ask about this question",
    askHint:
      "Ask what this question means, one question at a time. Plain Path does not remember earlier messages. Do not type your name, Social Security number, or other personal details.",
    askLabel: "Your question",
    askSend: "Ask",
    askEmpty: "Please type a question first.",
    askWaiting: "Plain Path is writing a reply…",
    askYou: "You asked:",
    askReplyLabel: "Plain Path:",
    askAiNote: "This reply was written by AI and was not checked by a person. It may be wrong.",
    askHelp: "Need a person? They can help for free:",
    askError: "Your question could not be sent. Please try again, or use the official instructions.",
    ssnWarning:
      "That looks like a Social Security number or another ID number. Your message was not sent. Please do not share personal information here.",

    doneTitle: "You reached the end",
    doneIntro:
      "You have read through every section. Plain Path did not fill out or send anything. To apply, use the official Arizona DES website.",
    review: "Go back to the sections",
    startOver: "Start over",
    newTab: "(opens in a new tab)",
  },

  es: {
    skip: "Saltar al contenido principal",
    tagline: "Un ayudante de IA para entender los formularios de desempleo",
    langLabel: "Idioma",
    disclaimer:
      "Plain Path es un prototipo estudiantil; no es asesoría legal y no está afiliado con Arizona DES.",
    loading: "Cargando…",
    loadError: "Plain Path no pudo cargar. Por favor, actualice la página.",

    welcomeTitle: "Bienvenido a Plain Path",
    welcomeIntro:
      "Plain Path explica en lenguaje sencillo las preguntas de la solicitud del seguro de desempleo de Arizona. Es solo una ayuda de lectura.",
    doesTitle: "Lo que hace",
    does1: "Muestra el texto oficial de cada pregunta, tal como está escrito.",
    does2: "Explica cada pregunta en lenguaje sencillo.",
    does3: "Indica lo que necesitará para responderla.",
    does4: "Le avisa cuándo es mejor consultar con una persona.",
    doesNotTitle: "Lo que no hace",
    doesNot1: "No llena ni envía su solicitud.",
    doesNot2: "No le dice si recibirá beneficios.",
    doesNot3: "No le dice qué responder. Sus respuestas deben ser suyas y deben ser verdaderas.",
    doesNot4: "No pide ni guarda su nombre, su número de Seguro Social ni ningún dato personal.",
    start: "Comenzar",

    intakeTitle: "Unas preguntas rápidas",
    intakeIntro:
      "Estas preguntas de sí o no solo deciden qué partes del recorrido verá. No se envían a ningún lugar y no deciden si puede recibir beneficios.",
    yes: "Sí",
    no: "No",
    intakeError: "Por favor, responda todas las preguntas para continuar.",
    back: "Atrás",
    next: "Continuar",

    docsTitle: "Haga una pausa y reúna sus documentos",
    docsIntro:
      "El formulario es más fácil con sus papeles a la mano. Marque cada cosa cuando la encuentre. Las marcas son solo un recordatorio para usted y se quedan en este dispositivo.",
    docsContinue: "Estoy listo. Mostrar las preguntas del formulario",

    progressTitle: "Su progreso",
    stepOf: "Sección {n} de {total}",
    statusDone: "terminada",
    statusCurrent: "usted está aquí",
    statusTodo: "sin empezar",
    questionN: "Pregunta {n}",
    officialLabel: "Texto oficial",
    officialOnlyEnglish: "El texto oficial solo está disponible en inglés.",
    plainLabel: "En palabras sencillas",
    needLabel: "Lo que necesitará",
    comingSoon: "Explicación próximamente. Consulte las instrucciones oficiales.",
    checkTitle: "Consulte con una persona",
    checkDefault:
      "Esta pregunta puede afectar su reclamo. Antes de responder, es buena idea hablar con la agencia o con ayuda legal. Pueden ayudarle gratis.",
    callLabel: "Llame al",
    sourceLabel: "Fuente",
    notListed:
      "¿Hay una pregunta de su formulario que no aparece aquí? Plain Path todavía no puede ayudar con esa pregunta. Por favor, use las instrucciones oficiales.",
    noQuestions: "Todavía no hay preguntas en esta sección.",
    prevSection: "Sección anterior",
    nextSection: "Sección siguiente",
    finish: "Terminar",

    askTitle: "Pregunte sobre esta pregunta",
    askHint:
      "Pregunte qué significa esta pregunta, una pregunta a la vez. Plain Path no recuerda los mensajes anteriores. No escriba su nombre, su número de Seguro Social ni otros datos personales.",
    askLabel: "Su pregunta",
    askSend: "Preguntar",
    askEmpty: "Por favor, escriba primero una pregunta.",
    askWaiting: "Plain Path está escribiendo una respuesta…",
    askYou: "Usted preguntó:",
    askReplyLabel: "Plain Path:",
    askAiNote: "Esta respuesta fue escrita por IA y no fue revisada por una persona. Puede tener errores.",
    askHelp: "¿Necesita hablar con una persona? Pueden ayudarle gratis:",
    askError: "No se pudo enviar su pregunta. Inténtelo de nuevo o use las instrucciones oficiales.",
    ssnWarning:
      "Eso parece un número de Seguro Social u otro número de identificación. Su mensaje no se envió. Por favor, no comparta información personal aquí.",

    doneTitle: "Llegó al final",
    doneIntro:
      "Ya leyó todas las secciones. Plain Path no llenó ni envió nada. Para solicitar, use el sitio web oficial de Arizona DES.",
    review: "Volver a las secciones",
    startOver: "Empezar de nuevo",
    newTab: "(se abre en una pestaña nueva)",
  },
};
