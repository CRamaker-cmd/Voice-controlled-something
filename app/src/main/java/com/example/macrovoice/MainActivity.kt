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
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*
import kotlin.math.roundToInt

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme { MacroApp() } }
    }
}

private fun isToday(millis: Long): Boolean {
    val a = Calendar.getInstance().apply { timeInMillis = millis }
    val b = Calendar.getInstance()
    return a.get(Calendar.YEAR) == b.get(Calendar.YEAR) &&
        a.get(Calendar.DAY_OF_YEAR) == b.get(Calendar.DAY_OF_YEAR)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MacroApp() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val store = remember { Store(context) }

    var meals by remember { mutableStateOf(store.meals()) }
    var text by remember { mutableStateOf("") }
    var listening by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var pending by remember { mutableStateOf<List<FoodItem>?>(null) }
    var showSettings by remember { mutableStateOf(store.apiKey.isBlank()) }
    var language by remember { mutableStateOf(store.language) }

    val voice = remember {
        VoiceInput(
            context,
            onPartial = { text = it },
            onFinal = { text = it },
            onError = { error = it },
            onListening = { listening = it },
        )
    }
    DisposableEffect(Unit) { onDispose { voice.stop() } }

    fun toggleMic() {
        if (listening) voice.stop() else { error = null; voice.start(language) }
    }

    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        if (it) toggleMic() else error = "Microphone permission is needed to talk to the app"
    }

    fun onMicClick() {
        val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) ==
            PackageManager.PERMISSION_GRANTED
        if (granted) toggleMic() else permission.launch(Manifest.permission.RECORD_AUDIO)
    }

    fun estimate() {
        if (store.apiKey.isBlank()) { showSettings = true; return }
        voice.stop()
        busy = true; error = null
        scope.launch {
            try {
                pending = MacroEstimator(store.apiKey).estimate(text)
            } catch (e: Exception) {
                error = e.message ?: "Something went wrong"
            } finally {
                busy = false
            }
        }
    }

    fun savePending() {
        val items = pending ?: return
        meals = (meals + Meal(System.currentTimeMillis(), System.currentTimeMillis(), text, items))
            .also(store::save)
        pending = null; text = ""
    }

    val today = meals.filter { isToday(it.timeMillis) }
    val timeFmt = remember { SimpleDateFormat("HH:mm", Locale.getDefault()) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("MacroVoice") },
                actions = {
                    IconButton(onClick = { showSettings = true }) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                },
            )
        },
    ) { pad ->
        LazyColumn(
            Modifier.padding(pad).padding(horizontal = 16.dp).fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item { TotalsCard("Today", today.sumOf { it.kcal }, today.sumOf { it.protein }, today.sumOf { it.carbs }, today.sumOf { it.fat }) }

            item {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    FilledIconButton(onClick = ::onMicClick, modifier = Modifier.size(64.dp)) {
                        Icon(if (listening) Icons.Default.Stop else Icons.Default.Mic, contentDescription = "Talk")
                    }
                    OutlinedTextField(
                        value = text,
                        onValueChange = { text = it },
                        modifier = Modifier.weight(1f),
                        placeholder = { Text("Tap the mic: \"2 loaves of AH volkoren…\"") },
                        minLines = 2,
                    )
                }
            }

            item {
                Button(onClick = ::estimate, enabled = text.isNotBlank() && !busy, modifier = Modifier.fillMaxWidth()) {
                    if (busy) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp) else Text("Estimate macros")
                }
                error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(top = 8.dp)) }
            }

            pending?.let { items ->
                item {
                    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)) {
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("Estimate", fontWeight = FontWeight.Bold)
                            items.forEach { ItemRow(it) }
                            HorizontalDivider()
                            Text(macroLine(items.sumOf { it.kcal }, items.sumOf { it.protein }, items.sumOf { it.carbs }, items.sumOf { it.fat }), fontWeight = FontWeight.Bold)
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(onClick = ::savePending) { Text("Save") }
                                OutlinedButton(onClick = { pending = null }) { Text("Discard") }
                            }
                        }
                    }
                }
            }

            item { Text("Logged today", style = MaterialTheme.typography.titleMedium) }
            items(today.sortedByDescending { it.timeMillis }, key = { it.id }) { meal ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("${timeFmt.format(Date(meal.timeMillis))}  ${meal.spoken}", Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
                            IconButton(onClick = { meals = (meals - meal).also(store::save) }) {
                                Icon(Icons.Default.Delete, contentDescription = "Delete")
                            }
                        }
                        meal.items.forEach { ItemRow(it) }
                        Text(macroLine(meal.kcal, meal.protein, meal.carbs, meal.fat), fontWeight = FontWeight.Medium)
                    }
                }
            }
            item { Spacer(Modifier.height(24.dp)) }
        }
    }

    if (showSettings) {
        var key by remember { mutableStateOf(store.apiKey) }
        AlertDialog(
            onDismissRequest = { showSettings = false },
            title = { Text("Settings") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    OutlinedTextField(key, { key = it }, label = { Text("Anthropic API key") }, singleLine = true)
                    Text("Speech language")
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf("en-US" to "English", "nl-NL" to "Nederlands").forEach { (tag, label) ->
                            FilterChip(selected = language == tag, onClick = { language = tag }, label = { Text(label) })
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { store.apiKey = key; store.language = language; showSettings = false }) { Text("Save") }
            },
        )
    }
}

private fun macroLine(kcal: Double, p: Double, c: Double, f: Double) =
    "${kcal.roundToInt()} kcal · P ${p.roundToInt()} g · C ${c.roundToInt()} g · F ${f.roundToInt()} g"

@Composable
private fun ItemRow(item: FoodItem) {
    Column {
        Text("${item.name} (${item.amount})", style = MaterialTheme.typography.bodyMedium)
        Text(macroLine(item.kcal, item.protein, item.carbs, item.fat), style = MaterialTheme.typography.bodySmall)
    }
}

@Composable
private fun TotalsCard(title: String, kcal: Double, p: Double, c: Double, f: Double) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.labelLarge)
            Text("${kcal.roundToInt()} kcal", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
            Text("Protein ${p.roundToInt()} g · Carbs ${c.roundToInt()} g · Fat ${f.roundToInt()} g")
        }
    }
}
