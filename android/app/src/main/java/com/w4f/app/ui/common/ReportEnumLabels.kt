package com.w4f.app.ui.common

import com.w4f.app.R
import com.w4f.app.domain.model.InterruptionFrequency
import com.w4f.app.domain.model.ProblemType
import com.w4f.app.domain.model.SeverityLevel
import com.w4f.app.domain.model.WaterSource

/** String-resource lookups for section 4's report enums — shared by the
 * "تبليغ جديد" stepper (step 2.3) and the home dossier list (step 2.4) so
 * the same label always means the same thing wherever a report shows up. */
fun WaterSource.labelRes(): Int =
  when (this) {
    WaterSource.NETWORK -> R.string.water_source_network
    WaterSource.WELL -> R.string.water_source_well
    WaterSource.SPRING -> R.string.water_source_spring
    WaterSource.TANK_TRUCK -> R.string.water_source_tank_truck
    WaterSource.RIVER -> R.string.water_source_river
    WaterSource.OTHER -> R.string.water_source_other
  }

fun ProblemType.labelRes(): Int =
  when (this) {
    ProblemType.NO_WATER -> R.string.problem_type_no_water
    ProblemType.INTERMITTENT -> R.string.problem_type_intermittent
    ProblemType.LOW_PRESSURE -> R.string.problem_type_low_pressure
    ProblemType.CONTAMINATION -> R.string.problem_type_contamination
    ProblemType.BROKEN_PUMP -> R.string.problem_type_broken_pump
    ProblemType.BROKEN_PIPE -> R.string.problem_type_broken_pipe
    ProblemType.DRY_SOURCE -> R.string.problem_type_dry_source
    ProblemType.OTHER -> R.string.problem_type_other
  }

fun InterruptionFrequency.labelRes(): Int =
  when (this) {
    InterruptionFrequency.PERMANENT -> R.string.frequency_permanent
    InterruptionFrequency.DAILY -> R.string.frequency_daily
    InterruptionFrequency.WEEKLY -> R.string.frequency_weekly
    InterruptionFrequency.MONTHLY -> R.string.frequency_monthly
    InterruptionFrequency.RARE -> R.string.frequency_rare
  }

fun SeverityLevel.labelRes(): Int =
  when (this) {
    SeverityLevel.LOW -> R.string.severity_low
    SeverityLevel.MEDIUM -> R.string.severity_medium
    SeverityLevel.HIGH -> R.string.severity_high
    SeverityLevel.CRITICAL -> R.string.severity_critical
  }
