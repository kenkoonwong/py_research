library(shiny)
library(dplyr)
library(readr)

# Define UI
ui <- fluidPage(
  titlePanel("Data Response Classifier"),

  sidebarLayout(
    sidebarPanel(
      fileInput("csv_file", "Choose CSV File",
                accept = c("text/csv", "text/comma-separated-values,text/plain", ".csv")),

      hr(),

      h4("Instructions:"),
      p("1. Upload a CSV with columns: id, name, value"),
      p("2. Review the data for each ID"),
      p("3. Click Positive or Negative"),
      p("4. Responses auto-save to result.csv"),

      hr(),

      textOutput("progress_text")
    ),

    mainPanel(
      h3(textOutput("current_id_text")),

      hr(),

      tableOutput("current_data_table"),

      hr(),

      fluidRow(
        column(6,
               actionButton("btn_positive", "Positive",
                          class = "btn-primary btn-lg btn-block",
                          icon = icon("thumbs-up"))),
        column(6,
               actionButton("btn_negative", "Negative",
                          class = "btn-danger btn-lg btn-block",
                          icon = icon("thumbs-down")))
      ),

      hr(),

      verbatimTextOutput("status_message")
    )
  )
)

# Define server logic
server <- function(input, output, session) {

  # Reactive values to store state
  rv <- reactiveValues(
    main_df = NULL,
    responses_df = NULL,
    processed_ids = c(),
    current_id = NULL,
    data_folder = NULL,
    result_file = "result.csv"
  )

  # Load existing result.csv if it exists
  load_existing_results <- function(folder_path) {
    result_path <- file.path(folder_path, rv$result_file)

    if (file.exists(result_path)) {
      tryCatch({
        existing_results <- read_csv(result_path, show_col_types = FALSE)

        if (all(c("id", "response") %in% colnames(existing_results))) {
          rv$responses_df <- existing_results
          rv$processed_ids <- existing_results$id
          return(TRUE)
        }
      }, error = function(e) {
        message("Warning: Could not load existing results: ", e$message)
      })
    }

    return(FALSE)
  }

  # Save to result.csv
  save_to_result_file <- function() {
    if (is.null(rv$data_folder)) return()

    result_path <- file.path(rv$data_folder, rv$result_file)

    tryCatch({
      write_csv(rv$responses_df, result_path)
    }, error = function(e) {
      showNotification(paste("Error saving to result.csv:", e$message),
                      type = "error")
    })
  }

  # Load next unprocessed ID
  load_next_id <- function() {
    if (is.null(rv$main_df)) return(FALSE)

    unique_ids <- unique(rv$main_df$id)
    unprocessed_ids <- setdiff(unique_ids, rv$processed_ids)

    if (length(unprocessed_ids) == 0) {
      showNotification("All IDs have been processed!", type = "message")
      rv$current_id <- NULL
      return(FALSE)
    }

    rv$current_id <- unprocessed_ids[1]
    return(TRUE)
  }

  # Handle CSV file upload
  observeEvent(input$csv_file, {
    req(input$csv_file)

    tryCatch({
      # Read the CSV
      df <- read_csv(input$csv_file$datapath, show_col_types = FALSE)

      # Validate columns
      required_cols <- c("id", "name", "value")
      if (!all(required_cols %in% colnames(df))) {
        showNotification(
          paste("CSV must contain columns:", paste(required_cols, collapse = ", ")),
          type = "error"
        )
        return()
      }

      rv$main_df <- df

      # Store the folder path
      rv$data_folder <- dirname(input$csv_file$datapath)
      # For user-selected files, use the directory where the file is located
      rv$data_folder <- dirname(normalizePath(input$csv_file$datapath))
      # Actually, for Shiny file uploads, save in current working directory
      rv$data_folder <- getwd()

      # Load existing results
      existing_found <- load_existing_results(rv$data_folder)

      if (existing_found) {
        num_existing <- length(rv$processed_ids)
        showNotification(
          paste0("Loaded ", nrow(df), " records\n",
                "Found existing result.csv with ", num_existing, " responses\n",
                "Filtering out already processed IDs..."),
          duration = 5,
          type = "message"
        )
      } else {
        # Initialize empty responses
        rv$responses_df <- tibble(id = numeric(), response = character())
        rv$processed_ids <- c()
        showNotification(paste("Loaded", nrow(df), "records"), type = "message")
      }

      # Load first ID
      load_next_id()

    }, error = function(e) {
      showNotification(paste("Error loading file:", e$message), type = "error")
    })
  })

  # Record positive response
  observeEvent(input$btn_positive, {
    req(rv$current_id)

    # Add response
    new_response <- tibble(id = rv$current_id, response = "positive")
    rv$responses_df <- bind_rows(rv$responses_df, new_response)
    rv$processed_ids <- c(rv$processed_ids, rv$current_id)

    # Save to file
    save_to_result_file()

    # Load next ID
    load_next_id()
  })

  # Record negative response
  observeEvent(input$btn_negative, {
    req(rv$current_id)

    # Add response
    new_response <- tibble(id = rv$current_id, response = "negative")
    rv$responses_df <- bind_rows(rv$responses_df, new_response)
    rv$processed_ids <- c(rv$processed_ids, rv$current_id)

    # Save to file
    save_to_result_file()

    # Load next ID
    load_next_id()
  })

  # Output: Current ID text
  output$current_id_text <- renderText({
    if (is.null(rv$current_id)) {
      "No ID loaded"
    } else {
      paste("ID:", rv$current_id)
    }
  })

  # Output: Current data table
  output$current_data_table <- renderTable({
    req(rv$main_df, rv$current_id)

    rv$main_df %>%
      filter(id == rv$current_id) %>%
      select(name, value)
  }, striped = TRUE, hover = TRUE, bordered = TRUE)

  # Output: Progress text
  output$progress_text <- renderText({
    if (is.null(rv$main_df)) {
      "No data loaded"
    } else {
      total_ids <- length(unique(rv$main_df$id))
      processed <- length(rv$processed_ids)
      paste0("Progress: ", processed, "/", total_ids, " IDs processed")
    }
  })

  # Output: Status message
  output$status_message <- renderText({
    if (is.null(rv$main_df)) {
      "Please upload a CSV file to begin."
    } else if (is.null(rv$current_id)) {
      paste0("All IDs processed!\n",
            "Responses saved to: ", file.path(rv$data_folder, rv$result_file))
    } else {
      paste0("Review the data above and click Positive or Negative.\n",
            "Auto-saving to: ", file.path(rv$data_folder, rv$result_file))
    }
  })
}

# Run the application
shinyApp(ui = ui, server = server)
