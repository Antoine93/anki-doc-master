# Optimisation Basic : Code

Règles spécifiques pour optimiser les cartes Q/R contenant du code.

## Préservation du code

- **Conserver** l'indentation exacte
- **Conserver** les blocs markdown (\`\`\`langage ... \`\`\`)
- **NE PAS** reformater ou "améliorer" le code

## Atomisation du code

### Bloc multi-concepts → plusieurs cartes

**Avant** :
```
Q: Expliquez ce code VHDL
R: ```vhdl
process(clk)
begin
  if rising_edge(clk) then
    state <= next_state;
    output <= compute_output(state);
  end if;
end process;
```
```

**Après** (2 cartes) :
```
Q: Comment déclarer un process synchrone en VHDL ?
R: ```vhdl
process(clk)
begin
  if rising_edge(clk) then
    -- logique synchrone
  end if;
end process;
```

Q: Comment mettre à jour l'état dans un process VHDL ?
R: ```vhdl
state <= next_state;
```
```

### Questions sur le code

Privilégier :
- "Que fait cette ligne ?" (1 ligne = 1 carte)
- "Quelle instruction pour X ?" → réponse = snippet minimal
- "Quel mot-clé pour X ?"

Éviter :
- "Expliquez ce code" (trop vague)
- Blocs >10 lignes dans une réponse
