package com.example.macrovoice

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlin.math.roundToInt

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme { MacroApp() } }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MacroApp(vm: MainViewModel = viewModel()) {
    val context = LocalContext.current
    var showSettings by remember { mutableStateOf(vm.store.serverUrl.isBlank()) }
    var language by remember { mutableStateOf(vm.store.language) }

    val voice = remember {
        VoiceInput(
            context,
            onPartial = { vm.draft = it },
            onFinal = { vm.submit(it) },            // no button: a finished sentence is recorded
            onError = { vm.setError(it) },
            onListening = { vm.listening = it },
        )
    }
    DisposableEffect(Unit) { onDispose { voice.stop() } }
    LaunchedEffect(Unit) { if (vm.store.serverUrl.isNotBlank()) vm.refresh() }

    fun toggleMic() {
        if (vm.listening) voice.stop() else { vm.setError(null); voice.start(language) }
    }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        if (it) toggleMic() else vm.setError("Microphone permission is needed to talk to the app")
    }
    fun onMicClick() {
        val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) ==
            PackageManager.PERMISSION_GRANTED
        if (granted) toggleMic() else permission.launch(Manifest.permission.RECORD_AUDIO)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("MacroVoice") },
                actions = {
                    IconButton(onClick = { showSettings = true }) { Icon(Icons.Default.Settings, "Settings") }
                },
            )
        },
    ) { pad ->
        LazyColumn(
            Modifier.padding(pad).padding(horizontal = 16.dp).fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilledIconButton(onClick = ::onMicClick, modifier = Modifier.size(64.dp)) {
                        Icon(if (vm.listening) Icons.Default.Stop else Icons.Default.Mic, "Talk")
                    }
                    OutlinedTextField(
                        value = vm.draft,
                        onValueChange = { vm.draft = it },
                        modifier = Modifier.weight(1f),
                        placeholder = { Text("Say or type what you ate") },
                        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                        keyboardActions = KeyboardActions(onSend = { vm.submit(vm.draft) }),
                        minLines = 2,
                    )
                    if (vm.busy) CircularProgressIndicator(Modifier.size(24.dp), strokeWidth = 2.dp)
                    else IconButton(onClick = { vm.submit(vm.draft) }, enabled = vm.draft.isNotBlank()) {
                        Icon(Icons.Default.Send, "Log")
                    }
                }
                vm.error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(top = 8.dp)) }
            }

            item {
                TabRow(selectedTabIndex = vm.period.ordinal) {
                    Period.values().forEach { t ->
                        Tab(selected = vm.period == t, onClick = { vm.selectPeriod(t) }, text = { Text(t.label) })
                    }
                }
            }

            item {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = { vm.shift(-1) }) { Icon(Icons.Default.ChevronLeft, "Previous") }
                    Text(
                        vm.stats?.let { if (it.start == it.end) it.start else "${it.start} – ${it.end}" } ?: "",
                        Modifier.weight(1f), style = MaterialTheme.typography.titleMedium,
                    )
                    TextButton(onClick = { vm.goToday() }) { Text("Today") }
                    IconButton(onClick = { vm.shift(1) }) { Icon(Icons.Default.ChevronRight, "Next") }
                }
            }

            vm.stats?.let { s ->
                item { StatsCard(s) }
                if (vm.period != Period.DAY) {
                    items(s.perDay, key = { it.date }) { d -> DayRow(d, s.perDay.maxOf { it.macros.kcal }) }
                }
            }

            if (vm.period == Period.DAY) {
                items(vm.entries, key = { it.id }) { e -> EntryCard(e, onDelete = { vm.delete(e.id) }) }
            }
            item { Spacer(Modifier.height(24.dp)) }
        }
    }

    if (showSettings) {
        var url by remember { mutableStateOf(vm.store.serverUrl) }
        var token by remember { mutableStateOf(vm.store.token) }
        AlertDialog(
            onDismissRequest = { showSettings = false },
            title = { Text("Settings") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    OutlinedTextField(url, { url = it }, label = { Text("Server address") },
                        placeholder = { Text("http://192.168.1.20:8000") }, singleLine = true)
                    OutlinedTextField(token, { token = it }, label = { Text("API token (if set)") }, singleLine = true)
                    Text("Speech language")
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf("en-US" to "English", "nl-NL" to "Nederlands").forEach { (tag, label) ->
                            FilterChip(selected = language == tag, onClick = { language = tag }, label = { Text(label) })
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    vm.store.serverUrl = url; vm.store.token = token; vm.store.language = language
                    showSettings = false; vm.refresh()
                }) { Text("Save") }
            },
        )
    }
}

private fun macroLine(m: Macros) =
    "${m.kcal.roundToInt()} kcal · P ${m.protein.roundToInt()} g · C ${m.carbs.roundToInt()} g · F ${m.fat.roundToInt()} g"

@Composable
private fun StatsCard(s: PeriodStats) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text("Total", style = MaterialTheme.typography.labelLarge)
            Text("${s.totals.kcal.roundToInt()} kcal", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
            Text("Protein ${s.totals.protein.roundToInt()} g · Carbs ${s.totals.carbs.roundToInt()} g · Fat ${s.totals.fat.roundToInt()} g")
            if (s.kind != "day") {
                s.avgPerLoggedDay?.let { Text("Avg per logged day (${s.daysLogged}): ${macroLine(it)}") }
                s.avgPerDay?.let { Text("Avg per day so far (${s.daysElapsed}): ${macroLine(it)}") }
            }
            if (s.proteinPct != null && s.carbsPct != null && s.fatPct != null) {
                Text("Energy split  P ${s.proteinPct.roundToInt()}% · C ${s.carbsPct.roundToInt()}% · F ${s.fatPct.roundToInt()}%")
            }
            if (s.unresolvedItems > 0) {
                Text("${s.unresolvedItems} item(s) could not be resolved and are not counted",
                    color = MaterialTheme.colorScheme.error)
            }
        }
    }
}

@Composable
private fun DayRow(d: DayStat, max: Double) {
    Column {
        Row {
            Text(d.date, Modifier.weight(1f))
            Text(if (d.logged) "${d.macros.kcal.roundToInt()} kcal" else "–")
        }
        LinearProgressIndicator(
            progress = { if (max > 0) (d.macros.kcal / max).toFloat() else 0f },
            modifier = Modifier.fillMaxWidth(),
        )
    }
}

@Composable
private fun EntryCard(e: Entry, onDelete: () -> Unit) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("“${e.rawText}”", Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
                IconButton(onClick = onDelete) { Icon(Icons.Default.Delete, "Delete") }
            }
            e.items.forEach { item ->
                Column {
                    Text("${item.name} (${item.amountText}${item.grams?.let { g -> ", ${g.roundToInt()} g" } ?: ""})",
                        style = MaterialTheme.typography.bodyMedium)
                    val m = item.macros
                    if (m != null) {
                        val tag = if (item.source == "ai") "  · AI estimate" else ""
                        Text(macroLine(m) + tag, style = MaterialTheme.typography.bodySmall)
                    } else {
                        Text("Not counted: ${item.note ?: "unresolved"}", style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.error)
                    }
                }
            }
            Text(macroLine(e.totals), fontWeight = FontWeight.Medium)
        }
    }
}
