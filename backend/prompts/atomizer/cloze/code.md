# Optimisation Cloze : Code

Règles spécifiques pour optimiser les cartes cloze contenant du code.

## Préservation

- **Conserver** l'indentation exacte
- **Conserver** les blocs markdown
- Les trous peuvent masquer des mots-clés, variables, valeurs

## Trous dans le code

✅ **Correct** (masquer mots-clés/variables) :
```
```vhdl
{{c1::process}}(clk)
begin
  if {{c2::rising_edge}}(clk) then
    state <= {{c3::next_state}};
  end if;
end process;
```
```

❌ **Éviter** (masquer syntaxe/structure) :
```
```vhdl
process(clk)
{{c1::begin}}
  if rising_edge(clk) {{c2::then}}
```
← trop fragmenté, perd le sens
```

## Atomisation

### Bloc avec trop de trous

**Avant** :
```
```python
def {{c1::calculate}}({{c2::x}}, {{c3::y}}):
    {{c4::result}} = {{c5::x}} + {{c6::y}}
    return {{c7::result}}
```
```

**Après** (2 cartes) :
```
```python
def {{c1::calculate}}(x, y):
    result = x + y
    return result
```

```python
def calculate({{c1::x}}, {{c2::y}}):
    result = {{c3::x + y}}
    return result
```
```

## Contexte

Ajouter du contexte si le code seul est ambigu :
```
[Python - addition]
result = {{c1::x + y}}
```
