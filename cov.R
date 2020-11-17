# Code for printing the evolution of covid19 cases in different cities/countries 
# from a specific date.
# The first plot generated is of all reported cases by the RIVM normalized by the 
# population and with a spline to follow the evolution better
# The second plot shows the evolution of the weekly cases for different countries 
# normalized by the population.

#Author: David Méndez

library(dplyr); library(ggplot2); library(lubridate)

## First plot

# User input for cities to consider and their population together with the start 
# date for the plot
pop <- data.frame(Municipality_name=c("Delft", "Zwolle","Breda"),
                  Population=c(101030, 123861,180937))
originDate <- ymd("2020-09-01")

# url to get the most updated data
url <- "https://data.rivm.nl/covid-19/COVID-19_aantallen_gemeente_per_dag.csv"

# data is stored in a tibble and time formatted
raw.data <- as_tibble(read.csv(url(url), sep=";"))
raw.data$Date_of_report <- ymd_hms(raw.data$Date_of_report)
raw.data$Date_of_publication <- ymd(raw.data$Date_of_publication)

# the data is filtered to keep the needed data for the plot and scaled 
filtered.data <- filter(raw.data,
                     Municipality_name %in% unique(pop$Municipality_name),
                     Date_of_publication>originDate)
final.data <- merge(filtered.data,pop)
final.data$case_per_100k <- final.data$Total_reported/final.data$Population*100000

# Amount of total cases is calculated from the raw data
total.data <- raw.data %>%
  filter(Date_of_publication>originDate) %>%
  group_by(Date_of_publication) %>%
  summarise(case_per_100k=sum(Total_reported)/172.8)
total.data$Municipality_name <- "Total"

# The filtered and total data are merged
print.data <- add_row(final.data,total.data)

# The publication day is logged and the plot is printed
dr <- final.data$Date_of_report[1]
qplot(x=Date_of_publication,
      y=case_per_100k,
      data=print.data, 
      color=Municipality_name,
      main=paste("Us versus them (data reported ",
                 paste(day(dr),
                       month(dr,label=T,abbr=T),
                       year(dr),sep="-"),
                 ")",
                 sep=""), 
      xlab="Date of publication",
      ylab="Positives per 100k tested")+
  geom_point()+geom_smooth(method="loess")

## Second plot

# User input for cities to consider and their population together with the start 
# date for the plot
countries <- c("Netherlands", "Spain", "France", 
               "Germany","Italy","United_States_of_America","United_Kingdom", "Austria")

# url to get the most updated data
url_pop <- "https://opendata.ecdc.europa.eu/covid19/casedistribution/csv/data.csv"

# data is stored in a tibble and time formatted
raw.count.data <- as_tibble(read.csv(url(url_pop), na.strings = "", fileEncoding = "UTF-8-BOM"))
raw.count.data$dateRep <- dmy(raw.count.data$dateRep)

# data is filter, week averages are calculated and scaled
final.c.data <- filter(raw.count.data,
                countriesAndTerritories %in% countries,
                dateRep>originDate) %>% 
                group_by(week = week(dateRep), countriesAndTerritories) %>% 
                summarise(date=mean(dateRep), 
                          case_per_100k = mean(cases)/mean(popData2019)*100000)

# The publication day is logged and the plot is printed
drc <- final.c.data$date[length(final.c.data$date)]
qplot(x=date,
      y=case_per_100k,
      data=final.c.data, 
      color=countriesAndTerritories,
      main=paste("World (data reported ",
                 paste(day(drc),
                       month(drc,label=T,abbr=T),
                       year(drc),sep="-"),
                 ")",
                 sep=""), 
      xlab="Date of publication",
      ylab="Positives per 100k tested")+
  geom_point()+geom_smooth(method="loess")


