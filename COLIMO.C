#include <stdio.h>
#include <stdlib.h>
#include <mysql/mysql.h>

// --- Prototypes ---
void ajouter();
void afficher();
void rechercher();
void modifier();
void supprimer();
void connexion();
void clean(char *s);

// --- Variables Globales ---
MYSQL *conn;
MYSQL_RES *res;
MYSQL_ROW row;

struct Machine {
    char emplacement[10];
    char type[50];
    char information[100];
    char ip[20];
    char systeme[50];
};

/* ---------------- CLEAN INPUT ---------------- */
void clean(char *s) {
    for(int i=0; s[i]; i++)
        if(s[i]=='\'') s[i]=' ';
}

/* ---------------- CONNEXION ---------------- */
void connexion() {
    conn = mysql_init(NULL);
    if(conn == NULL) { printf("Erreur mysql_init\n"); exit(1); }
    if(mysql_real_connect(conn, "localhost", "root", "hiba1234", "pack_informatique", 3306, NULL, 0) == NULL) {
        printf("%s\n", mysql_error(conn));
        exit(1);
    }
}

/* ---------------- AJOUTER ---------------- */
void ajouter() {
    struct Machine m;
    char req[500];
    printf("\nEmplacement : "); scanf("%s", m.emplacement);
    getchar(); printf("Type : "); scanf(" %[^\n]", m.type);
    getchar(); printf("Information : "); scanf(" %[^\n]", m.information);
    printf("Adresse IP : "); scanf("%s", m.ip);
    getchar(); printf("Systeme : "); scanf(" %[^\n]", m.systeme);
    clean(m.type); clean(m.information); clean(m.systeme);
    sprintf(req, "INSERT INTO machine(emplacement,type_machine,information,adresse_ip,systeme_exploitation) VALUES('%s','%s','%s','%s','%s')",
            m.emplacement, m.type, m.information, m.ip, m.systeme);
    if(mysql_query(conn, req) == 0) {
        printf("\nAjout reussi.\n");
        mysql_query(conn, "SELECT * FROM machine");
        res = mysql_store_result(conn);
        if (res != NULL) {
            printf("Nombre total de lignes : %d\n", (int)mysql_num_rows(res));
            mysql_free_result(res);
        }
    } else printf("Erreur : %s\n", mysql_error(conn));
}

/* ---------------- AFFICHER ---------------- */
void afficher() {
    if(mysql_query(conn, "SELECT * FROM machine") == 0) {
        res = mysql_store_result(conn);
        
        // 1. العنوان (Header)
        printf("\n+------+-------------+-----------------+---------------------------+-----------------+-----------------+\n");
        printf("| Code | Emplacement | Type            | Information               | Adresse IP      | Systeme         |\n");
        printf("+------+-------------+-----------------+---------------------------+-----------------+-----------------+\n");
        
        // 2. البيانات (داخل الـ Loop)
        while((row = mysql_fetch_row(res))) {
            printf("| %-4s | %-11s | %-15s | %-25s | %-15s | %-15s |\n", 
                   row[0], row[1], row[2], row[3], row[4], row[5]);
        }
        
        // 3. الخط التحتاني (خاصو يكون خارج اللوب باش يترسم مرة وحدة!)
        printf("+------+-------------+-----------------+---------------------------+-----------------+-----------------+\n");
        
        mysql_free_result(res);
    } else {
        printf("Erreur : %s\n", mysql_error(conn));
    }
}
/* ---------------- SUPPRIMER ---------------- */
void supprimer() {
    int code; char req[100];
    printf("Code machine a supprimer : "); scanf("%d", &code);
    sprintf(req, "DELETE FROM machine WHERE code_machine=%d", code);
    if(mysql_query(conn, req) == 0) {
        if(mysql_affected_rows(conn) > 0) printf("Suppression reussie. ✅\n");
        else printf("Aucune machine trouvée avec ce code.\n");
    } else printf("Erreur : %s\n", mysql_error(conn));
}

/* ---------------- MAIN ---------------- */
int main() {
    int choix;
    connexion();
    do {
        printf("\n==============================\n PACK INFORMATIQUE \n==============================\n");
        printf("1. Ajouter\n2. Afficher\n3. Rechercher\n4. Modifier\n5. Supprimer\n6. Quitter\nVotre choix : ");
        scanf("%d", &choix);
        switch(choix) {
            case 1: ajouter(); break;
            case 2: afficher(); break;
            case 3: rechercher(); break;
            case 4: modifier(); break;
            case 5: supprimer(); break;
            case 6: break;
            default: printf("Choix incorrect.\n");
        }
    } while(choix != 6);
    mysql_close(conn);
    return 0;
}